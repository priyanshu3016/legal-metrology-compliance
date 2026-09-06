"""
test_step7.py - Step 7 Compliance Rules Engine integration test.

Verifies:
  POST /api/v1/inspections/{id}/compliance  (run engine)
  GET  /api/v1/inspections/{id}/compliance  (read result)
  Fully compliant inspection -> COMPLIANT, score=100
  Missing declarations -> NON_COMPLIANT, violations persisted
  Correct score calculation
  Violations in SQLite
  No duplicate violations on repeated calls
  404 on nonexistent inspection

Run from backend/ directory:
    venv\\Scripts\\python.exe test_step7.py
"""
import os
import sqlite3
import subprocess
import sys
import time

import httpx

BASE_URL = "http://127.0.0.1:8010"
REF_COMPLIANT  = "LM-COMP-PASS-001"
REF_PARTIAL    = "LM-COMP-FAIL-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ok(label: str) -> None:
    print(f"  [PASS] {label}")


def fail(label: str, detail: str = "") -> None:
    print(f"  [FAIL] {label}{': ' + detail if detail else ''}")


def assert_status(label: str, r: httpx.Response, expected: int) -> bool:
    if r.status_code == expected:
        ok(f"{label} -> HTTP {r.status_code}")
        return True
    fail(label, f"expected {expected}, got {r.status_code}. Body: {r.text[:400]}")
    return False


def assert_eq(label: str, actual, expected) -> bool:
    if actual == expected:
        ok(label)
        return True
    fail(label, f"expected {expected!r}, got {actual!r}")
    return False


def assert_true(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        ok(label)
        return True
    fail(label, detail)
    return False


def cleanup_inspections(base: str, refs: list[str]) -> None:
    r = httpx.get(f"{base}/api/v1/inspections?limit=200", timeout=10)
    if r.status_code == 200:
        for item in r.json():
            if item["reference_number"] in refs:
                httpx.delete(f"{base}/api/v1/inspections/{item['id']}", timeout=10)


def create_inspection(base: str, ref: str) -> int:
    r = httpx.post(f"{base}/api/v1/inspections", json={
        "reference_number": ref,
        "location": "Test Lab",
    }, timeout=10)
    assert r.status_code == 201, f"Could not create inspection: {r.text}"
    return r.json()["id"]


def submit_extraction(base: str, inspection_id: int, payload: dict) -> None:
    r = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/extracted-data",
        json=payload,
        timeout=10,
    )
    assert r.status_code == 200, f"Extraction failed: {r.text}"


# ---------------------------------------------------------------------------
# Full compliance payload (all 10 rules should PASS)
# ---------------------------------------------------------------------------
FULL_PAYLOAD = {
    "product_name":          "Tata Salt",
    "manufacturer":          "Tata Consumer Products Ltd.",
    "net_quantity":          "1 kg",
    "mrp":                   "Rs.30",
    "date_of_manufacturing": "06/2026",
    "date_of_packing":       "08/2026",
    "best_before":           "6 months",
    "consumer_care":         "1800-123-4567",
    "country_of_origin":     "India",
    "unit_sale_price":       "30.00",
    "confidence": {
        "product_name": 0.99,
        "net_quantity":  0.98,
        "mrp":           0.97,
    },
}

# Partial payload: only 3 fields provided — 7 rules should FAIL
PARTIAL_PAYLOAD = {
    "product_name":      "Unknown Brand",
    "net_quantity":      "500 g",
    "country_of_origin": "India",
}


# ---------------------------------------------------------------------------
# Test sequence
# ---------------------------------------------------------------------------

def run_tests(base: str) -> bool:
    all_passed = True
    db_path = os.path.abspath("packcheck.db")

    # ── 0. Pre-test cleanup ───────────────────────────────────────────────
    print("\n[0] Pre-test cleanup")
    cleanup_inspections(base, [REF_COMPLIANT, REF_PARTIAL])
    print("  Cleanup done")

    # ══════════════════════════════════════════════════════════════════════
    # TEST A: Fully compliant inspection
    # ══════════════════════════════════════════════════════════════════════
    print("\n[A] Fully compliant inspection")

    a_id = create_inspection(base, REF_COMPLIANT)
    print(f"  Created inspection id={a_id}")
    submit_extraction(base, a_id, FULL_PAYLOAD)
    print("  Submitted full extraction")

    # Run compliance engine
    r_comp = httpx.post(
        f"{base}/api/v1/inspections/{a_id}/compliance", timeout=10
    )
    all_passed &= assert_status("POST compliance (full)", r_comp, 200)
    body = r_comp.json()

    all_passed &= assert_eq("  overall_status = COMPLIANT", body["overall_status"], "COMPLIANT")
    all_passed &= assert_eq("  score = 100.0", body["score"], 100.0)
    all_passed &= assert_eq("  total_checks = 10", body["total_checks"], 10)
    all_passed &= assert_eq("  passed_checks = 10", body["passed_checks"], 10)
    all_passed &= assert_eq("  failed_checks = 0", body["failed_checks"], 0)
    all_passed &= assert_eq("  violations list empty", body["violations"], [])
    all_passed &= assert_eq("  checks list length", len(body["checks"]), 10)

    # Verify inspection updated in DB
    r_insp = httpx.get(f"{base}/api/v1/inspections/{a_id}", timeout=10)
    assert r_insp.status_code == 200
    insp = r_insp.json()
    all_passed &= assert_eq("  inspection.compliance_score = 100.0", insp["compliance_score"], 100.0)
    all_passed &= assert_eq("  inspection.status = compliant", insp["status"], "compliant")

    # GET compliance
    r_get = httpx.get(f"{base}/api/v1/inspections/{a_id}/compliance", timeout=10)
    all_passed &= assert_status("GET compliance (full)", r_get, 200)
    get_body = r_get.json()
    all_passed &= assert_eq("  GET overall_status = COMPLIANT", get_body["overall_status"], "COMPLIANT")
    all_passed &= assert_eq("  GET score = 100.0", get_body["score"], 100.0)

    # SQLite: violations table should have 0 rows for this inspection
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM violations WHERE inspection_id=?", (a_id,))
    viol_count_a = cur.fetchone()[0]
    con.close()
    all_passed &= assert_eq("  SQLite violations count = 0", viol_count_a, 0)

    # ══════════════════════════════════════════════════════════════════════
    # TEST B: Partially compliant inspection (missing 7 fields)
    # ══════════════════════════════════════════════════════════════════════
    print("\n[B] Partially compliant inspection (7 fields missing)")

    b_id = create_inspection(base, REF_PARTIAL)
    print(f"  Created inspection id={b_id}")
    submit_extraction(base, b_id, PARTIAL_PAYLOAD)
    print("  Submitted partial extraction")

    r_comp_b = httpx.post(
        f"{base}/api/v1/inspections/{b_id}/compliance", timeout=10
    )
    all_passed &= assert_status("POST compliance (partial)", r_comp_b, 200)
    body_b = r_comp_b.json()

    all_passed &= assert_eq("  overall_status = NON_COMPLIANT", body_b["overall_status"], "NON_COMPLIANT")

    # Fields provided: product_name, net_quantity, country_of_origin -> 3 PASS
    # unit_sale_price absent -> PASS (optional)  -> 4 PASS total
    # Expected: 4 PASS, 6 FAIL -> score = 40.0
    all_passed &= assert_eq("  passed_checks = 4", body_b["passed_checks"], 4)
    all_passed &= assert_eq("  failed_checks = 6", body_b["failed_checks"], 6)
    expected_score = round(4 / 10 * 100, 2)
    all_passed &= assert_eq(f"  score = {expected_score}", body_b["score"], expected_score)
    all_passed &= assert_eq("  violations count = 6", len(body_b["violations"]), 6)

    # Verify inspection updated
    r_insp_b = httpx.get(f"{base}/api/v1/inspections/{b_id}", timeout=10)
    insp_b = r_insp_b.json()
    all_passed &= assert_eq("  inspection.status = non_compliant", insp_b["status"], "non_compliant")
    all_passed &= assert_eq("  inspection.compliance_score", insp_b["compliance_score"], expected_score)

    # SQLite: violations count
    con2 = sqlite3.connect(db_path)
    cur2 = con2.cursor()
    cur2.execute("SELECT COUNT(*) FROM violations WHERE inspection_id=?", (b_id,))
    viol_count_b = cur2.fetchone()[0]
    cur2.execute("SELECT field_name, severity, description FROM violations WHERE inspection_id=? ORDER BY field_name", (b_id,))
    viol_rows_b = cur2.fetchall()
    con2.close()
    all_passed &= assert_eq("  SQLite violations count = 6", viol_count_b, 6)
    print(f"  Violations in SQLite:")
    for fn, sev, desc in viol_rows_b:
        print(f"    [{sev.upper()}] {fn}: {desc[:60]}")

    # Check violation field names
    viol_fields = {row[0] for row in viol_rows_b}
    expected_fail_fields = {
        "manufacturer", "mrp", "date_of_manufacturing",
        "date_of_packing", "best_before", "consumer_care",
    }
    all_passed &= assert_eq("  violated fields match", viol_fields, expected_fail_fields)

    # ══════════════════════════════════════════════════════════════════════
    # TEST C: No duplicate violations on repeated POST
    # ══════════════════════════════════════════════════════════════════════
    print("\n[C] Repeated compliance check -> no duplicate violations")

    r_comp_b2 = httpx.post(
        f"{base}/api/v1/inspections/{b_id}/compliance", timeout=10
    )
    all_passed &= assert_status("POST compliance (2nd run)", r_comp_b2, 200)

    r_comp_b3 = httpx.post(
        f"{base}/api/v1/inspections/{b_id}/compliance", timeout=10
    )
    all_passed &= assert_status("POST compliance (3rd run)", r_comp_b3, 200)

    con3 = sqlite3.connect(db_path)
    cur3 = con3.cursor()
    cur3.execute("SELECT COUNT(*) FROM violations WHERE inspection_id=?", (b_id,))
    viol_count_after_repeat = cur3.fetchone()[0]
    con3.close()
    all_passed &= assert_eq(
        "  Violations after 3 runs = 6 (no duplicates)",
        viol_count_after_repeat, 6,
    )

    # ══════════════════════════════════════════════════════════════════════
    # TEST D: 404 on nonexistent inspection
    # ══════════════════════════════════════════════════════════════════════
    print("\n[D] 404 on nonexistent inspection")
    r_404_post = httpx.post(f"{base}/api/v1/inspections/999999/compliance", timeout=10)
    all_passed &= assert_status("POST compliance nonexistent -> 404", r_404_post, 404)
    r_404_get = httpx.get(f"{base}/api/v1/inspections/999999/compliance", timeout=10)
    all_passed &= assert_status("GET compliance nonexistent -> 404", r_404_get, 404)

    # ══════════════════════════════════════════════════════════════════════
    # TEST E: GET compliance on a fresh inspection (no POST ever called)
    # ══════════════════════════════════════════════════════════════════════
    print("\n[E] GET compliance on fresh full inspection (no POST compliance)")
    e_ref = "LM-COMP-GET-001"
    cleanup_inspections(base, [e_ref])
    e_id = create_inspection(base, e_ref)
    submit_extraction(base, e_id, FULL_PAYLOAD)

    r_get_e = httpx.get(
        f"{base}/api/v1/inspections/{e_id}/compliance", timeout=10
    )
    all_passed &= assert_status("GET compliance (fresh, no POST)", r_get_e, 200)
    all_passed &= assert_eq("  GET overall_status = COMPLIANT", r_get_e.json()["overall_status"], "COMPLIANT")
    all_passed &= assert_eq("  GET score = 100.0", r_get_e.json()["score"], 100.0)

    # Clean up E inspection
    httpx.delete(f"{base}/api/v1/inspections/{e_id}", timeout=10)
    print("  Cleaned up inspection E")


    # ══════════════════════════════════════════════════════════════════════
    # TEST F: Cleanup + cascade verify
    # ══════════════════════════════════════════════════════════════════════
    print("\n[F] Cleanup")
    for iid, ref in [(a_id, REF_COMPLIANT), (b_id, REF_PARTIAL)]:
        r_del = httpx.delete(f"{base}/api/v1/inspections/{iid}", timeout=10)
        all_passed &= assert_status(f"Delete inspection {ref}", r_del, 200)

    con4 = sqlite3.connect(db_path)
    cur4 = con4.cursor()
    cur4.execute(
        "SELECT COUNT(*) FROM violations WHERE inspection_id IN (?, ?)", (a_id, b_id)
    )
    remaining = cur4.fetchone()[0]
    con4.close()
    all_passed &= assert_eq("  Violations CASCADE deleted", remaining, 0)

    return all_passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("STEP 7 - COMPLIANCE RULES ENGINE INTEGRATION TEST")
    print("=" * 60)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8010"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    passed = False
    try:
        time.sleep(5)
        passed = run_tests(BASE_URL)
    except Exception as exc:
        print(f"\n  [ERROR] {exc}")
        import traceback; traceback.print_exc()
    finally:
        proc.terminate()
        _out, _err = proc.communicate(timeout=10)
        startup_ok = "Application startup complete" in _err

    print("\n" + "=" * 60)
    print(f"  Server startup  : {'PASS' if startup_ok else 'FAIL'}")
    print(f"  All tests       : {'PASS' if passed else 'FAIL'}")
    print("=" * 60)
    print("OVERALL:", "PASS" if (startup_ok and passed) else "FAIL")
    sys.exit(0 if (startup_ok and passed) else 1)


if __name__ == "__main__":
    main()

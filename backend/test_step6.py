"""
test_step6.py - Step 6 AI/OCR extracted-data integration test.

Verifies:
  POST /api/v1/inspections/{id}/extracted-data  (submit)
  GET  /api/v1/inspections/{id}/extracted-data  (retrieve)
  Upsert behavior (field update, not duplication)
  Confidence storage and retrieval
  Empty payload rejection (422)
  Confidence out-of-range rejection (422)
  Missing inspection rejection (404)
  Inspection status transitions (pending -> processing -> completed)

Run from backend/ directory:
    venv\\Scripts\\python.exe test_step6.py
"""
import io
import os
import subprocess
import sys
import time

import httpx

BASE_URL = "http://127.0.0.1:8009"
TEST_REF = "LM-OCR-TEST-001"

PASS = "PASS"
FAIL = "FAIL"


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


def assert_in(label: str, key, container) -> bool:
    if key in container:
        ok(label)
        return True
    fail(label, f"{key!r} not found in {container!r}")
    return False


# ---------------------------------------------------------------------------
# Test sequence
# ---------------------------------------------------------------------------

def run_tests(base: str) -> bool:
    all_passed = True

    # ── 0. Pre-test cleanup ──────────────────────────────────────────────
    print("\n[0] Pre-test cleanup")
    r_list = httpx.get(f"{base}/api/v1/inspections?limit=200", timeout=10)
    if r_list.status_code == 200:
        for item in r_list.json():
            if item["reference_number"] == TEST_REF:
                httpx.delete(f"{base}/api/v1/inspections/{item['id']}", timeout=10)
                print(f"  Removed leftover inspection id={item['id']}")
    print("  Cleanup done")

    # ── 1. Create test inspection ────────────────────────────────────────
    print("\n[1] Create test inspection")
    r = httpx.post(f"{base}/api/v1/inspections", json={
        "reference_number": TEST_REF,
        "location": "Test Lab",
    }, timeout=10)
    if not assert_status("Create inspection", r, 201):
        return False
    inspection_id = r.json()["id"]
    all_passed &= assert_eq("  initial status", r.json()["status"], "pending")
    print(f"  Created inspection id={inspection_id}")

    # ── 2. GET before any extraction -> empty data ───────────────────────
    print("\n[2] GET extracted-data before submission -> empty")
    r_empty = httpx.get(
        f"{base}/api/v1/inspections/{inspection_id}/extracted-data", timeout=10
    )
    all_passed &= assert_status("GET before submission", r_empty, 200)
    body = r_empty.json()
    all_passed &= assert_eq("  extracted_data is empty dict", body["extracted_data"], {})
    all_passed &= assert_eq("  declarations list is empty", body["declarations"], [])

    # ── 3. POST extracted data ───────────────────────────────────────────
    print("\n[3] POST extracted-data")
    payload1 = {
        "product_name": "Tata Salt",
        "manufacturer": "Tata Consumer Products Ltd.",
        "net_quantity": "1 kg",
        "mrp": "Rs.30",
        "date_of_packing": "08/2026",
        "best_before": "6 months",
        "consumer_care": "1800-123-4567",
        "country_of_origin": "India",
        "confidence": {
            "product_name": 0.98,
            "net_quantity": 0.99,
            "mrp": 0.97,
            "manufacturer": 0.94,
        },
    }
    r_post = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/extracted-data",
        json=payload1,
        timeout=10,
    )
    all_passed &= assert_status("POST extracted-data", r_post, 200)
    post_body = r_post.json()

    all_passed &= assert_eq("  inspection_id in response", post_body["inspection_id"], inspection_id)
    all_passed &= assert_eq("  extraction_status", post_body["extraction_status"], "completed")

    ed = post_body["extracted_data"]
    all_passed &= assert_eq("  product_name stored", ed.get("product_name"), "Tata Salt")
    all_passed &= assert_eq("  net_quantity stored", ed.get("net_quantity"), "1 kg")
    all_passed &= assert_eq("  mrp stored", ed.get("mrp"), "Rs.30")
    all_passed &= assert_eq("  country_of_origin stored", ed.get("country_of_origin"), "India")

    conf = post_body["confidence"]
    all_passed &= assert_eq("  confidence product_name", conf.get("product_name"), 0.98)
    all_passed &= assert_eq("  confidence net_quantity", conf.get("net_quantity"), 0.99)
    all_passed &= assert_eq("  confidence mrp", conf.get("mrp"), 0.97)

    decls = post_body["declarations"]
    all_passed &= assert_eq("  8 declaration rows", len(decls), 8)

    # ── 4. GET extracted-data -> same data ──────────────────────────────
    print("\n[4] GET extracted-data -> verify persisted")
    r_get = httpx.get(
        f"{base}/api/v1/inspections/{inspection_id}/extracted-data", timeout=10
    )
    all_passed &= assert_status("GET extracted-data", r_get, 200)
    get_body = r_get.json()
    all_passed &= assert_eq("  product_name matches", get_body["extracted_data"].get("product_name"), "Tata Salt")
    all_passed &= assert_eq("  confidence net_quantity matches", get_body["confidence"].get("net_quantity"), 0.99)
    all_passed &= assert_eq("  extraction_status", get_body["extraction_status"], "completed")

    # ── 5. Verify in SQLite via inspection detail ────────────────────────
    print("\n[5] Verify declarations in GET /inspections/{id}")
    r_det = httpx.get(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
    all_passed &= assert_status("GET inspection detail", r_det, 200)
    det = r_det.json()
    all_passed &= assert_eq("  inspection status = completed", det["status"], "completed")
    all_passed &= assert_eq("  declarations list has 8 rows", len(det["declarations"]), 8)
    field_names_in_detail = {d["field_name"] for d in det["declarations"]}
    all_passed &= assert_in("  product_name in declarations", "product_name", field_names_in_detail)
    all_passed &= assert_in("  mrp in declarations", "mrp", field_names_in_detail)

    # ── 6. Upsert: re-submit with updated value for existing field ───────
    print("\n[6] Upsert: re-submit updated mrp value")
    payload2 = {
        "mrp": "Rs.35",       # updated
        "brand": "Tata",      # new field
        "confidence": {
            "mrp": 0.99,
            "brand": 0.95,
        },
    }
    r_post2 = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/extracted-data",
        json=payload2,
        timeout=10,
    )
    all_passed &= assert_status("POST upsert", r_post2, 200)
    upsert_body = r_post2.json()

    # mrp updated
    all_passed &= assert_eq("  mrp updated to Rs.35", upsert_body["extracted_data"].get("mrp"), "Rs.35")
    # brand added
    all_passed &= assert_eq("  brand added", upsert_body["extracted_data"].get("brand"), "Tata")
    # product_name untouched
    all_passed &= assert_eq("  product_name untouched", upsert_body["extracted_data"].get("product_name"), "Tata Salt")

    # verify no duplicate: total declarations should be 9 (8 original + 1 new brand)
    all_passed &= assert_eq("  total declarations = 9 (no duplicates)", len(upsert_body["declarations"]), 9)

    # ── 7. Confirm mrp count in SQLite = 1 (not 2) ──────────────────────
    print("\n[7] SQLite direct check: mrp declaration count = 1")
    import sqlite3
    db_path = os.path.abspath("packcheck.db")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM declarations WHERE inspection_id=? AND field_name='mrp'",
        (inspection_id,),
    )
    mrp_count = cur.fetchone()[0]
    all_passed &= assert_eq("  mrp row count in SQLite", mrp_count, 1)
    cur.execute(
        "SELECT value FROM declarations WHERE inspection_id=? AND field_name='mrp'",
        (inspection_id,),
    )
    mrp_value = cur.fetchone()[0]
    all_passed &= assert_eq("  mrp value in SQLite", mrp_value, "Rs.35")
    con.close()
    ok(f"  SQLite direct check passed: mrp count={mrp_count}, value={mrp_value!r}")

    # ── 8. Validation: empty payload -> 422 ────────────────────────────
    print("\n[8] Validation tests")
    r_empty_payload = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/extracted-data",
        json={},
        timeout=10,
    )
    all_passed &= assert_status("Empty payload -> 422", r_empty_payload, 422)

    # ── 9. Validation: confidence out-of-range -> 422 ──────────────────
    r_bad_conf = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/extracted-data",
        json={"product_name": "X", "confidence": {"product_name": 1.5}},
        timeout=10,
    )
    all_passed &= assert_status("Confidence > 1.0 -> 422", r_bad_conf, 422)

    r_neg_conf = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/extracted-data",
        json={"product_name": "X", "confidence": {"product_name": -0.1}},
        timeout=10,
    )
    all_passed &= assert_status("Confidence < 0.0 -> 422", r_neg_conf, 422)

    # ── 10. Validation: non-existent inspection -> 404 ──────────────────
    r_404 = httpx.post(
        f"{base}/api/v1/inspections/999999/extracted-data",
        json={"product_name": "X"},
        timeout=10,
    )
    all_passed &= assert_status("Non-existent inspection -> 404", r_404, 404)

    r_get_404 = httpx.get(
        f"{base}/api/v1/inspections/999999/extracted-data", timeout=10
    )
    all_passed &= assert_status("GET non-existent inspection -> 404", r_get_404, 404)

    # ── 11. Cleanup ──────────────────────────────────────────────────────
    print("\n[11] Cleanup test inspection")
    r_del = httpx.delete(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
    all_passed &= assert_status("Delete test inspection (cascades declarations)", r_del, 200)

    # Verify declarations gone from SQLite
    con2 = sqlite3.connect(db_path)
    cur2 = con2.cursor()
    cur2.execute(
        "SELECT COUNT(*) FROM declarations WHERE inspection_id=?",
        (inspection_id,),
    )
    remaining = cur2.fetchone()[0]
    con2.close()
    all_passed &= assert_eq("  declarations CASCADE deleted", remaining, 0)

    return all_passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("STEP 6 - AI/OCR EXTRACTION INTEGRATION TEST")
    print("=" * 55)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8009"],
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

    print("\n" + "=" * 55)
    print(f"  Server startup  : {'PASS' if startup_ok else 'FAIL'}")
    print(f"  All tests       : {'PASS' if passed else 'FAIL'}")
    print("=" * 55)
    print("OVERALL:", "PASS" if (startup_ok and passed) else "FAIL")
    sys.exit(0 if (startup_ok and passed) else 1)


if __name__ == "__main__":
    main()

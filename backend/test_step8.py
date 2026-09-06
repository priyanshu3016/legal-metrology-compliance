"""
test_step8.py - Step 8 Evidence and Report generation integration test.

Verifies:
  Part A - Evidence:
    POST /api/v1/inspections/{id}/evidence      -> 201
    GET  /api/v1/inspections/{id}/evidence      -> 200
    DELETE /api/v1/evidence/{id}                -> 200
    404 on nonexistent inspection

  Part B - Reports:
    POST /api/v1/inspections/{id}/report        -> 201, PDF exists on disk
    GET  /api/v1/inspections/{id}/reports       -> 200 list
    GET  /api/v1/reports/{id}/download          -> 200, application/pdf
    SHA-256 hash present in response
    Report record in SQLite
    Nonexistent inspection -> 404

Run from backend/ directory:
    venv\\Scripts\\python.exe test_step8.py
"""
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8011"
TEST_REF = "LM-STEP8-TEST-001"

FULL_EXTRACTION = {
    "product_name":          "Amul Butter",
    "manufacturer":          "Gujarat Cooperative Milk Marketing Federation",
    "net_quantity":          "500 g",
    "mrp":                   "Rs.290",
    "date_of_packing":       "09/2026",
    "date_of_manufacturing": "09/2026",
    "best_before":           "6 months",
    "consumer_care":         "1800-258-3333",
    "country_of_origin":     "India",
    "unit_sale_price":       "290.00",
    "confidence": {"product_name": 0.99, "net_quantity": 0.98},
}


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


def cleanup(base: str, ref: str) -> None:
    r = httpx.get(f"{base}/api/v1/inspections?limit=200", timeout=10)
    if r.status_code == 200:
        for item in r.json():
            if item["reference_number"] == ref:
                httpx.delete(f"{base}/api/v1/inspections/{item['id']}", timeout=10)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_tests(base: str) -> bool:
    all_passed = True
    db_path = os.path.abspath("packcheck.db")

    # ── 0. Pre-test cleanup ───────────────────────────────────────────────
    print("\n[0] Pre-test cleanup")
    cleanup(base, TEST_REF)
    print("  Cleanup done")

    # ── 1. Create test inspection ─────────────────────────────────────────
    print("\n[1] Create test inspection")
    r = httpx.post(f"{base}/api/v1/inspections", json={
        "reference_number": TEST_REF,
        "location": "Test Lab - Step 8",
    }, timeout=10)
    all_passed &= assert_status("Create inspection", r, 201)
    iid = r.json()["id"]
    print(f"  inspection id={iid}")

    # ── 2. Submit extraction ──────────────────────────────────────────────
    print("\n[2] Submit extraction data")
    r_ex = httpx.post(
        f"{base}/api/v1/inspections/{iid}/extracted-data",
        json=FULL_EXTRACTION, timeout=10,
    )
    all_passed &= assert_status("Submit extraction", r_ex, 200)

    # ── 3. Run compliance ─────────────────────────────────────────────────
    print("\n[3] Run compliance")
    r_comp = httpx.post(f"{base}/api/v1/inspections/{iid}/compliance", timeout=10)
    all_passed &= assert_status("POST compliance", r_comp, 200)
    all_passed &= assert_eq("  overall_status COMPLIANT", r_comp.json()["overall_status"], "COMPLIANT")

    # ══════════════════════════════════════════════════════════════════════
    # PART A — Evidence
    # ══════════════════════════════════════════════════════════════════════

    # ── 4. Create evidence ────────────────────────────────────────────────
    print("\n[4] POST evidence")
    r_ev1 = httpx.post(f"{base}/api/v1/inspections/{iid}/evidence", json={
        "description": "MRP clearly visible in top-right corner",
        "field_name": "mrp",
        "confidence": 0.97,
    }, timeout=10)
    all_passed &= assert_status("POST evidence #1", r_ev1, 201)
    ev1 = r_ev1.json()
    all_passed &= assert_eq("  field_name", ev1["field_name"], "mrp")
    all_passed &= assert_eq("  confidence", ev1["confidence"], 0.97)
    ev1_id = ev1["id"]

    r_ev2 = httpx.post(f"{base}/api/v1/inspections/{iid}/evidence", json={
        "description": "Net quantity label on back panel",
        "field_name": "net_quantity",
        "bounding_box": {"x": 100, "y": 200, "w": 80, "h": 20},
    }, timeout=10)
    all_passed &= assert_status("POST evidence #2 (with bounding_box)", r_ev2, 201)
    ev2_id = r_ev2.json()["id"]
    all_passed &= assert_eq("  bounding_box stored", r_ev2.json()["bounding_box"], {"x": 100, "y": 200, "w": 80, "h": 20})

    # 404 on nonexistent inspection
    r_ev_404 = httpx.post(f"{base}/api/v1/inspections/999999/evidence", json={
        "description": "x"
    }, timeout=10)
    all_passed &= assert_status("POST evidence nonexistent -> 404", r_ev_404, 404)

    # ── 5. GET evidence ───────────────────────────────────────────────────
    print("\n[5] GET evidence")
    r_list = httpx.get(f"{base}/api/v1/inspections/{iid}/evidence", timeout=10)
    all_passed &= assert_status("GET evidence list", r_list, 200)
    all_passed &= assert_eq("  2 evidence records", len(r_list.json()), 2)

    # ── 6. DELETE evidence ────────────────────────────────────────────────
    print("\n[6] DELETE evidence")
    r_del_ev = httpx.delete(f"{base}/api/v1/evidence/{ev1_id}", timeout=10)
    all_passed &= assert_status("DELETE evidence #1", r_del_ev, 200)
    all_passed &= assert_eq("  deleted id", r_del_ev.json()["id"], ev1_id)

    # Verify gone
    r_list2 = httpx.get(f"{base}/api/v1/inspections/{iid}/evidence", timeout=10)
    all_passed &= assert_eq("  1 evidence record remains", len(r_list2.json()), 1)

    # 404 on nonexistent evidence
    r_del_404 = httpx.delete(f"{base}/api/v1/evidence/999999", timeout=10)
    all_passed &= assert_status("DELETE nonexistent evidence -> 404", r_del_404, 404)

    # SQLite: evidence count = 1
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM evidence WHERE inspection_id=?", (iid,))
    ev_count = cur.fetchone()[0]
    con.close()
    all_passed &= assert_eq("  SQLite evidence count = 1", ev_count, 1)

    # ══════════════════════════════════════════════════════════════════════
    # PART B — Report generation
    # ══════════════════════════════════════════════════════════════════════

    # ── 7. Generate PDF report ────────────────────────────────────────────
    print("\n[7] POST report (PDF generation)")
    r_rep = httpx.post(
        f"{base}/api/v1/inspections/{iid}/report", timeout=30
    )
    all_passed &= assert_status("POST report", r_rep, 201)
    rep = r_rep.json()
    print(f"  report_id={rep['report_id']} file={rep['file_name']}")

    all_passed &= assert_true("  report_id present", bool(rep.get("report_id")))
    all_passed &= assert_true("  file_name ends .pdf", rep["file_name"].endswith(".pdf"))
    all_passed &= assert_true("  sha256 present (64 hex chars)", len(rep.get("sha256", "")) == 64)
    all_passed &= assert_true("  download_url present", "/download" in rep.get("download_url", ""))

    # ── 8. Verify PDF on disk ─────────────────────────────────────────────
    print("\n[8] Verify PDF on disk")
    reports_dir = Path("reports")
    pdf_path = reports_dir / rep["file_name"]
    all_passed &= assert_true("  PDF file exists on disk", pdf_path.exists(), str(pdf_path))
    if pdf_path.exists():
        all_passed &= assert_true("  PDF size > 0", pdf_path.stat().st_size > 0)
        # Verify SHA-256 matches
        import hashlib
        h = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        all_passed &= assert_eq("  SHA-256 matches", h, rep["sha256"])

    # ── 9. Verify report in SQLite ────────────────────────────────────────
    print("\n[9] SQLite report record")
    con2 = sqlite3.connect(db_path)
    cur2 = con2.cursor()
    cur2.execute(
        "SELECT id, file_path, file_hash FROM reports WHERE inspection_id=?",
        (iid,),
    )
    row = cur2.fetchone()
    con2.close()
    all_passed &= assert_true("  report row exists in SQLite", row is not None)
    if row:
        all_passed &= assert_true("  file_hash stored", bool(row[2]))
        all_passed &= assert_eq("  file_hash matches", row[2], rep["sha256"])

    # ── 10. List reports ───────────────────────────────────────────────────
    print("\n[10] GET reports list")
    r_list_rep = httpx.get(f"{base}/api/v1/inspections/{iid}/reports", timeout=10)
    all_passed &= assert_status("GET reports list", r_list_rep, 200)
    all_passed &= assert_eq("  1 report in list", len(r_list_rep.json()), 1)

    # ── 11. Download PDF ───────────────────────────────────────────────────
    print("\n[11] GET report download")
    report_id = rep["report_id"]
    r_dl = httpx.get(f"{base}/api/v1/reports/{report_id}/download", timeout=30)
    all_passed &= assert_status("GET download", r_dl, 200)
    all_passed &= assert_true(
        "  Content-Type is application/pdf",
        "application/pdf" in r_dl.headers.get("content-type", ""),
    )
    all_passed &= assert_true("  Response body > 1 KB", len(r_dl.content) > 1024)
    # PDF magic bytes
    all_passed &= assert_true(
        "  PDF magic bytes %PDF",
        r_dl.content[:4] == b"%PDF",
    )

    # 404 on nonexistent report download
    r_dl_404 = httpx.get(f"{base}/api/v1/reports/999999/download", timeout=10)
    all_passed &= assert_status("Download nonexistent report -> 404", r_dl_404, 404)

    # 404 on nonexistent inspection report list
    r_rep_404 = httpx.get(f"{base}/api/v1/inspections/999999/reports", timeout=10)
    all_passed &= assert_status("GET reports nonexistent inspection -> 404", r_rep_404, 404)

    # ── 12. Cleanup ────────────────────────────────────────────────────────
    print("\n[12] Cleanup")
    r_del_insp = httpx.delete(f"{base}/api/v1/inspections/{iid}", timeout=10)
    all_passed &= assert_status("Delete test inspection (cascades)", r_del_insp, 200)

    # Verify evidence and reports cascaded
    con3 = sqlite3.connect(db_path)
    cur3 = con3.cursor()
    cur3.execute("SELECT COUNT(*) FROM evidence WHERE inspection_id=?", (iid,))
    ev_remaining = cur3.fetchone()[0]
    cur3.execute("SELECT COUNT(*) FROM reports WHERE inspection_id=?", (iid,))
    rep_remaining = cur3.fetchone()[0]
    con3.close()
    all_passed &= assert_eq("  Evidence CASCADE deleted", ev_remaining, 0)
    all_passed &= assert_eq("  Reports CASCADE deleted", rep_remaining, 0)

    # Clean up PDF file
    if pdf_path.exists():
        pdf_path.unlink()
        print(f"  Deleted PDF: {pdf_path}")

    return all_passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("STEP 8 - EVIDENCE & REPORT GENERATION INTEGRATION TEST")
    print("=" * 60)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8011"],
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

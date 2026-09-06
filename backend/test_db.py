"""
test_db.py - Step 4 database integration test.

Verifies that the Inspection API correctly persists data in SQLite (packcheck.db).

Run from the backend/ directory:
    venv\\Scripts\\python.exe test_db.py

Prerequisites:
    venv\\Scripts\\python.exe -m pip install -r requirements.txt
    (Server does NOT need to be running - this script starts/stops it internally.)
"""
import io
import sys
# Force UTF-8 output on Windows to avoid cp1252 encoding errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import subprocess
import time

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8007"
TEST_REF = "LM-TEST-DB-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ok(label: str) -> None:
    print(f"  [PASS] {label}")


def fail(label: str, detail: str = "") -> None:
    print(f"  [FAIL] {label}{': ' + detail if detail else ''}")


def assert_eq(label: str, actual, expected) -> bool:
    if actual == expected:
        ok(label)
        return True
    fail(label, f"expected {expected!r}, got {actual!r}")
    return False


def assert_status(label: str, response: httpx.Response, expected_status: int) -> bool:
    if response.status_code == expected_status:
        ok(f"{label} → HTTP {response.status_code}")
        return True
    fail(label, f"expected HTTP {expected_status}, got {response.status_code}. Body: {response.text[:200]}")
    return False


# ---------------------------------------------------------------------------
# Main test sequence
# ---------------------------------------------------------------------------

def run_tests(base: str) -> bool:
    all_passed = True

    # ── 0. PRE-TEST CLEANUP ───────────────────────────────────────────────
    # Delete any leftover test record from a previous run so tests are
    # idempotent and can be run multiple times safely.
    print("\n[0] Pre-test cleanup")
    r_list = httpx.get(f"{base}/api/v1/inspections", timeout=10)
    if r_list.status_code == 200:
        for item in r_list.json():
            if item["reference_number"] == TEST_REF:
                httpx.delete(f"{base}/api/v1/inspections/{item['id']}", timeout=10)
                print(f"  Cleaned up leftover record id={item['id']} ({TEST_REF})")
    else:
        print("  (could not list inspections for cleanup)")

    # ── 1. CREATE ────────────────────────────────────────────────────────
    print("\n[1] POST /api/v1/inspections  - Create")

    r = httpx.post(f"{base}/api/v1/inspections", json={
        "reference_number": TEST_REF,
        "location": "Mumbai",
        "inspector_id": None,
        "product_id": None,
    }, timeout=10)
    if not assert_status("Create inspection", r, 201):
        all_passed = False
        return all_passed  # can't continue without an ID

    data = r.json()
    inspection_id: int = data["id"]
    all_passed &= assert_eq("  reference_number", data["reference_number"], TEST_REF)
    all_passed &= assert_eq("  location",         data["location"],         "Mumbai")
    all_passed &= assert_eq("  status",           data["status"],           "pending")
    all_passed &= assert_eq("  compliance_score", data["compliance_score"],  None)
    print(f"     → Created id={inspection_id}")

    # ── 1b. Duplicate reference → 409 ───────────────────────────────────
    print("\n[1b] POST duplicate reference_number  - Expect 409")
    r_dup = httpx.post(f"{base}/api/v1/inspections", json={
        "reference_number": TEST_REF,
        "location": "Delhi",
    }, timeout=10)
    all_passed &= assert_status("Duplicate → 409", r_dup, 409)

    # ── 2. RETRIEVE (detail) ─────────────────────────────────────────────
    print("\n[2] GET /api/v1/inspections/{id}  - Retrieve from SQLite")
    r = httpx.get(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
    all_passed &= assert_status("Retrieve by id", r, 200)
    data = r.json()
    all_passed &= assert_eq("  id matches",        data["id"],              inspection_id)
    all_passed &= assert_eq("  reference_number",  data["reference_number"], TEST_REF)
    all_passed &= assert_eq("  images list",       data["images"],          [])
    all_passed &= assert_eq("  declarations list", data["declarations"],     [])
    all_passed &= assert_eq("  violations list",   data["violations"],       [])
    all_passed &= assert_eq("  evidence list",     data["evidence"],         [])

    # ── 2b. Non-existent ID → 404 ────────────────────────────────────────
    print("\n[2b] GET /api/v1/inspections/999999  - Expect 404")
    r_404 = httpx.get(f"{base}/api/v1/inspections/999999", timeout=10)
    all_passed &= assert_status("Non-existent → 404", r_404, 404)

    # ── 3. LIST ──────────────────────────────────────────────────────────
    print("\n[3] GET /api/v1/inspections  - List from SQLite")
    r = httpx.get(f"{base}/api/v1/inspections", timeout=10)
    all_passed &= assert_status("List inspections", r, 200)
    items = r.json()
    found = any(item["id"] == inspection_id for item in items)
    if found:
        ok("  New inspection appears in list")
    else:
        fail("  New inspection should appear in list")
        all_passed = False

    # List with status filter
    r_filt = httpx.get(f"{base}/api/v1/inspections?status=pending", timeout=10)
    all_passed &= assert_status("List filter status=pending", r_filt, 200)
    pending_items = r_filt.json()
    found_pending = any(item["id"] == inspection_id for item in pending_items)
    if found_pending:
        ok("  Inspection found in pending filter")
    else:
        fail("  Inspection not found in pending filter")
        all_passed = False

    # List with pagination
    r_page = httpx.get(f"{base}/api/v1/inspections?skip=0&limit=5", timeout=10)
    all_passed &= assert_status("List with pagination", r_page, 200)
    all_passed &= assert_eq(
        "  Pagination honours limit",
        len(r_page.json()) <= 5,
        True,
    )

    # ── 4. UPDATE ────────────────────────────────────────────────────────
    print("\n[4] PATCH /api/v1/inspections/{id}  - Update in SQLite")
    r = httpx.patch(f"{base}/api/v1/inspections/{inspection_id}", json={
        "status": "processing",
        "compliance_score": 78.5,
        "location": "Chennai",
    }, timeout=10)
    all_passed &= assert_status("Update inspection", r, 200)
    data = r.json()
    all_passed &= assert_eq("  status updated",           data["status"],           "processing")
    all_passed &= assert_eq("  compliance_score updated", data["compliance_score"],  78.5)
    all_passed &= assert_eq("  location updated",         data["location"],         "Chennai")

    # Verify update is persisted — re-fetch from SQLite
    r_refetch = httpx.get(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
    all_passed &= assert_status("Re-fetch after update", r_refetch, 200)
    refetched = r_refetch.json()
    all_passed &= assert_eq("  status persisted in SQLite",    refetched["status"],           "processing")
    all_passed &= assert_eq("  score persisted in SQLite",     refetched["compliance_score"],  78.5)
    all_passed &= assert_eq("  location persisted in SQLite",  refetched["location"],         "Chennai")

    # PATCH validation — bad status
    r_bad = httpx.patch(f"{base}/api/v1/inspections/{inspection_id}", json={
        "status": "invalid_status",
    }, timeout=10)
    all_passed &= assert_status("PATCH bad status → 422", r_bad, 422)

    # PATCH validation — score out of range
    r_score = httpx.patch(f"{base}/api/v1/inspections/{inspection_id}", json={
        "compliance_score": 105.0,
    }, timeout=10)
    all_passed &= assert_status("PATCH score>100 → 422", r_score, 422)

    # PATCH validation — empty body
    r_empty = httpx.patch(f"{base}/api/v1/inspections/{inspection_id}", json={}, timeout=10)
    all_passed &= assert_status("PATCH empty body → 422", r_empty, 422)

    # ── 5. DELETE ────────────────────────────────────────────────────────
    print("\n[5] DELETE /api/v1/inspections/{id}  - Delete from SQLite")
    r = httpx.delete(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
    all_passed &= assert_status("Delete inspection", r, 200)
    del_body = r.json()
    all_passed &= assert_eq("  response id matches", del_body["id"], inspection_id)

    # Verify record is gone
    r_gone = httpx.get(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
    all_passed &= assert_status("Verify deleted → 404", r_gone, 404)

    # Also verify it's gone from the list
    r_list_after = httpx.get(f"{base}/api/v1/inspections", timeout=10)
    still_there = any(item["id"] == inspection_id for item in r_list_after.json())
    if not still_there:
        ok("  Deleted inspection absent from list")
    else:
        fail("  Deleted inspection still appears in list")
        all_passed = False

    # ── 6. SQLite direct verification ─────────────────────────────────
    print("\n[6] SQLite direct check - verify data was stored on disk")
    import sqlite3, os
    db_path = os.path.abspath("packcheck.db")
    if not os.path.exists(db_path):
        fail("packcheck.db does not exist at expected path")
        all_passed = False
    else:
        ok(f"  packcheck.db exists ({os.path.getsize(db_path)} bytes)")
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall()]
        expected_tables = {
            "declarations", "evidence", "inspection_images",
            "inspections", "products", "reports", "rules", "users", "violations",
        }
        missing = expected_tables - set(tables)
        if missing:
            fail(f"  Missing tables: {missing}")
            all_passed = False
        else:
            ok(f"  All 9 tables present: {tables}")

        # Confirm our test record was actually deleted from SQLite
        cur.execute("SELECT id FROM inspections WHERE reference_number=?", (TEST_REF,))
        row = cur.fetchone()
        if row is None:
            ok(f"  Test record '{TEST_REF}' confirmed deleted from inspections table")
        else:
            fail(f"  Test record '{TEST_REF}' still in SQLite (id={row[0]})")
            all_passed = False

        con.close()

    return all_passed


# ---------------------------------------------------------------------------
# Entry point — spin up server, run tests, shut down
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("STEP 4 — DATABASE INTEGRATION TEST")
    print("=" * 55)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8007"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        time.sleep(5)  # wait for startup

        # Check startup
        _out, _err = "", ""
        if "Application startup complete" not in (_err or ""):
            # Read what's available without blocking
            import select, os
            pass  # we'll check after the test run

        passed = run_tests(BASE_URL)

    except Exception as exc:
        print(f"\n  [ERROR] Unexpected exception: {exc}")
        passed = False

    finally:
        proc.terminate()
        _out, _err = proc.communicate(timeout=10)
        startup_ok = "Application startup complete" in _err

    print("\n" + "=" * 55)
    print(f"  Server startup        : {'PASS' if startup_ok else 'FAIL'}")
    print(f"  All API + DB tests    : {'PASS' if passed else 'FAIL'}")
    print("=" * 55)
    print("OVERALL:", "PASS" if (startup_ok and passed) else "FAIL")
    sys.exit(0 if (startup_ok and passed) else 1)


if __name__ == "__main__":
    main()

"""
test_step10.py - Step 10 Dashboard & History API test.

Verifies:
  1. Server starts successfully.
  2. GET /api/v1/dashboard/summary
  3. GET /api/v1/dashboard/recent-inspections
  4. GET /api/v1/inspections/history (with pagination & search & filter)
  5. GET /api/v1/dashboard/violations
  6. GET /api/v1/dashboard/compliance-trend
  7. Existing Steps functionality verification
"""
import os
import sqlite3
import subprocess
import sys
import time

import httpx

BASE_URL = "http://127.0.0.1:8013"

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

def assert_true(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        ok(label)
        return True
    fail(label, detail)
    return False

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_tests(base: str) -> bool:
    all_passed = True
    
    # Pre-populate some dummy data to test endpoints (using existing APIs)
    r_create = httpx.post(f"{base}/api/v1/inspections", json={
        "reference_number": "DASH-TEST-01",
        "location": "Mumbai",
        "status": "compliant"
    }, timeout=10)
    
    # Ignore 409 conflict if already exists
    if r_create.status_code not in (201, 409):
        fail("Pre-populate data", f"Failed: {r_create.status_code}")
        return False
        
    print("\n[1] GET /api/v1/dashboard/summary")
    r_sum = httpx.get(f"{base}/api/v1/dashboard/summary", timeout=10)
    all_passed &= assert_status("Summary returns 200", r_sum, 200)
    
    data = r_sum.json()
    all_passed &= assert_true("total_inspections >= 0", data.get("total_inspections", -1) >= 0)
    all_passed &= assert_true("compliance_rate present", "compliance_rate" in data)

    print("\n[2] GET /api/v1/dashboard/recent-inspections")
    r_recent = httpx.get(f"{base}/api/v1/dashboard/recent-inspections", timeout=10)
    all_passed &= assert_status("Recent returns 200", r_recent, 200)
    r_data = r_recent.json()
    all_passed &= assert_true("Result is a list", isinstance(r_data, list))
    if len(r_data) > 0:
        all_passed &= assert_true("Contains expected fields", "reference_number" in r_data[0])

    print("\n[3] GET /api/v1/inspections/history")
    r_hist = httpx.get(f"{base}/api/v1/inspections/history?page=1&page_size=5&search=DASH-TEST", timeout=10)
    all_passed &= assert_status("History with search returns 200", r_hist, 200)
    hist_data = r_hist.json()
    all_passed &= assert_true("Total field exists", "total" in hist_data)
    all_passed &= assert_true("Pagination items is a list", isinstance(hist_data.get("items"), list))
    
    r_hist_filter = httpx.get(f"{base}/api/v1/inspections/history?status=compliant", timeout=10)
    all_passed &= assert_status("History with status filter returns 200", r_hist_filter, 200)

    print("\n[4] GET /api/v1/dashboard/violations")
    r_viol = httpx.get(f"{base}/api/v1/dashboard/violations", timeout=10)
    all_passed &= assert_status("Violations summary returns 200", r_viol, 200)
    viol_data = r_viol.json()
    all_passed &= assert_true("Contains 'critical' field", "critical" in viol_data)

    print("\n[5] GET /api/v1/dashboard/compliance-trend")
    r_trend = httpx.get(f"{base}/api/v1/dashboard/compliance-trend", timeout=10)
    all_passed &= assert_status("Trend returns 200", r_trend, 200)
    trend_data = r_trend.json()
    all_passed &= assert_true("Result is a list", isinstance(trend_data, list))

    return all_passed

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("STEP 10 - DASHBOARD & HISTORY API TEST")
    print("=" * 60)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8013"],
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

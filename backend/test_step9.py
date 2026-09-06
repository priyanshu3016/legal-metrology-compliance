"""
test_step9.py - Step 9 Inspector/User Authentication API test.

Verifies:
  1. Demo user creation / existence
  2. Successful login (POST /api/v1/auth/login)
  3. Invalid login is rejected
  4. Valid bearer token works with /auth/me (GET /api/v1/auth/me)
  5. Logout invalidates the token (POST /api/v1/auth/logout)
  6. Invalid/expired token is rejected
"""
import os
import sqlite3
import subprocess
import sys
import time

import httpx

BASE_URL = "http://127.0.0.1:8012"

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

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_tests(base: str) -> bool:
    all_passed = True

    print("\n[1] Check Database for Demo User")
    db_path = os.path.abspath("packcheck.db")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT id, username, is_active FROM users WHERE username='inspector'")
    row = cur.fetchone()
    con.close()
    
    all_passed &= assert_true("Demo user exists in DB", row is not None)
    if row:
        all_passed &= assert_eq("Demo user is active", row[2], 1)

    print("\n[2] Invalid Login")
    r_inv = httpx.post(f"{base}/api/v1/auth/login", json={
        "username": "inspector",
        "password": "wrongpassword"
    }, timeout=10)
    all_passed &= assert_status("Reject invalid password", r_inv, 401)

    r_inv2 = httpx.post(f"{base}/api/v1/auth/login", json={
        "username": "notfounduser",
        "password": "password"
    }, timeout=10)
    all_passed &= assert_status("Reject unknown username", r_inv2, 401)

    print("\n[3] Successful Login")
    r_login = httpx.post(f"{base}/api/v1/auth/login", json={
        "username": "inspector",
        "password": "inspector123"
    }, timeout=10)
    all_passed &= assert_status("Login successful", r_login, 200)
    data = r_login.json()
    all_passed &= assert_true("Token is present", "token" in data and len(data["token"]) > 10)
    all_passed &= assert_eq("Success flag is True", data.get("success"), True)
    
    token = data.get("token", "")
    headers = {"Authorization": f"Bearer {token}"}

    print("\n[4] Get Current User (/auth/me)")
    r_me = httpx.get(f"{base}/api/v1/auth/me", headers=headers, timeout=10)
    all_passed &= assert_status("/auth/me with valid token", r_me, 200)
    me_data = r_me.json()
    all_passed &= assert_eq("Username matches", me_data.get("username"), "inspector")
    all_passed &= assert_true("Password hash is NOT returned", "password_hash" not in me_data)

    print("\n[5] Missing or Invalid Token")
    r_no_tok = httpx.get(f"{base}/api/v1/auth/me", timeout=10)
    all_passed &= assert_status("/auth/me with no token -> 403", r_no_tok, 403)
    
    r_bad_tok = httpx.get(f"{base}/api/v1/auth/me", headers={"Authorization": "Bearer badtoken"}, timeout=10)
    all_passed &= assert_status("/auth/me with bad token -> 401", r_bad_tok, 401)

    print("\n[6] Logout")
    r_logout = httpx.post(f"{base}/api/v1/auth/logout", headers=headers, timeout=10)
    all_passed &= assert_status("Logout successful", r_logout, 200)
    
    r_me_after = httpx.get(f"{base}/api/v1/auth/me", headers=headers, timeout=10)
    all_passed &= assert_status("/auth/me after logout -> 401", r_me_after, 401)

    return all_passed

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("STEP 9 - AUTHENTICATION API TEST")
    print("=" * 60)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8012"],
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

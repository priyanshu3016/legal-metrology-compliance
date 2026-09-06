"""
test_step5.py - Step 5 image upload integration test.

Verifies:
  - POST /api/v1/inspections/{id}/images   (upload)
  - GET  /api/v1/inspections/{id}/images   (list)
  - GET  /api/v1/inspections/{id}          (detail includes image)
  - DELETE /api/v1/inspections/{id}/images/{image_id}  (delete DB + file)
  - Physical file created on disk, then removed after delete.

Run from backend/ directory:
    venv\\Scripts\\python.exe test_step5.py
"""
import io
import os
import subprocess
import sys
import time

import httpx

BASE_URL = "http://127.0.0.1:8008"
TEST_REF = "LM-IMG-TEST-001"

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
    fail(label, f"expected {expected}, got {r.status_code}. Body: {r.text[:300]}")
    return False


def assert_eq(label: str, actual, expected) -> bool:
    if actual == expected:
        ok(label)
        return True
    fail(label, f"expected {expected!r}, got {actual!r}")
    return False


def make_test_image(width: int = 8, height: int = 8) -> bytes:
    """
    Generate a minimal valid PNG in pure Python (no Pillow needed).
    The PNG is a solid red 8x8 image.
    """
    import struct, zlib

    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    # IHDR: width, height, bit_depth=8, color_type=2 (RGB)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)

    # Image data: each row is filter_byte(0) + RGB pixels
    raw_row = b"\x00" + b"\xff\x00\x00" * width  # red pixels
    raw_data = raw_row * height
    idat = chunk(b"IDAT", zlib.compress(raw_data))

    iend = chunk(b"IEND", b"")

    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_tests(base: str) -> bool:
    all_passed = True

    # ── 0. Cleanup any leftover test data ────────────────────────────────
    print("\n[0] Pre-test cleanup")
    r_list = httpx.get(f"{base}/api/v1/inspections?limit=200", timeout=10)
    if r_list.status_code == 200:
        for item in r_list.json():
            if item["reference_number"] == TEST_REF:
                httpx.delete(f"{base}/api/v1/inspections/{item['id']}", timeout=10)
                print(f"  Removed leftover inspection id={item['id']}")
    print("  Cleanup done")

    # ── 1. Create a test inspection ──────────────────────────────────────
    print("\n[1] Create test inspection")
    r = httpx.post(f"{base}/api/v1/inspections", json={
        "reference_number": TEST_REF,
        "location": "Test Lab",
    }, timeout=10)
    if not assert_status("Create inspection", r, 201):
        return False
    inspection_id = r.json()["id"]
    print(f"  Created inspection id={inspection_id}")

    # ── 2. Upload a valid PNG ─────────────────────────────────────────────
    print("\n[2] Upload a valid PNG image")
    png_bytes = make_test_image()
    r_up = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/images",
        files=[("files", ("test_label.png", io.BytesIO(png_bytes), "image/png"))],
        data={"panel_type": "front"},
        timeout=10,
    )
    all_passed &= assert_status("Upload PNG", r_up, 201)
    if r_up.status_code != 201:
        # can't proceed without an image record
        httpx.delete(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
        return False

    upload_data = r_up.json()
    all_passed &= assert_eq("  uploaded count", upload_data["uploaded"], 1)
    images_in_response = upload_data["images"]
    all_passed &= assert_eq("  images list length", len(images_in_response), 1)

    img_record = images_in_response[0]
    image_id = img_record["id"]
    file_path_rel = img_record["file_path"]   # e.g. "uploads/inspection_1_<uuid>.png"
    all_passed &= assert_eq("  panel_type", img_record["panel_type"], "front")
    all_passed &= assert_eq("  inspection_id", img_record["inspection_id"], inspection_id)
    print(f"  Image id={image_id}, path={file_path_rel}")

    # ── 3. Verify physical file exists ───────────────────────────────────
    print("\n[3] Verify physical file created on disk")
    abs_path = os.path.abspath(file_path_rel)  # relative to backend/
    if os.path.exists(abs_path):
        size = os.path.getsize(abs_path)
        ok(f"  File exists: {abs_path} ({size} bytes)")
    else:
        fail("  Physical file not found on disk", abs_path)
        all_passed = False

    # ── 4. Verify in SQLite via inspection detail ─────────────────────────
    print("\n[4] Verify image appears in GET /inspections/{id}")
    r_det = httpx.get(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
    all_passed &= assert_status("GET inspection detail", r_det, 200)
    detail = r_det.json()
    found_in_detail = any(img["id"] == image_id for img in detail.get("images", []))
    if found_in_detail:
        ok("  Image present in inspection detail")
    else:
        fail("  Image NOT found in inspection detail")
        all_passed = False

    # ── 5. List images endpoint ──────────────────────────────────────────
    print("\n[5] GET /inspections/{id}/images")
    r_imgs = httpx.get(f"{base}/api/v1/inspections/{inspection_id}/images", timeout=10)
    all_passed &= assert_status("List images", r_imgs, 200)
    imgs_list = r_imgs.json()
    all_passed &= assert_eq("  list length >= 1", len(imgs_list) >= 1, True)
    found_in_list = any(img["id"] == image_id for img in imgs_list)
    if found_in_list:
        ok("  Uploaded image found in list")
    else:
        fail("  Uploaded image NOT found in list")
        all_passed = False

    # ── 6. Upload a second image (multi-upload) ──────────────────────────
    print("\n[6] Upload a second image (to verify multi-upload)")
    r_up2 = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/images",
        files=[("files", ("back_label.png", io.BytesIO(make_test_image()), "image/png"))],
        data={"panel_type": "back"},
        timeout=10,
    )
    all_passed &= assert_status("Upload second PNG", r_up2, 201)
    image_id2 = r_up2.json()["images"][0]["id"] if r_up2.status_code == 201 else None

    r_list2 = httpx.get(f"{base}/api/v1/inspections/{inspection_id}/images", timeout=10)
    if r_list2.status_code == 200:
        all_passed &= assert_eq("  total images now 2", len(r_list2.json()), 2)

    # ── 7. Rejection tests ───────────────────────────────────────────────
    print("\n[7] Rejection tests")

    # 7a: disallowed file type
    r_bad_ext = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/images",
        files=[("files", ("document.pdf", io.BytesIO(b"%PDF-1.4 bad"), "application/pdf"))],
        timeout=10,
    )
    all_passed &= assert_status("Reject PDF -> 400", r_bad_ext, 400)

    # 7b: empty file
    r_empty = httpx.post(
        f"{base}/api/v1/inspections/{inspection_id}/images",
        files=[("files", ("empty.png", io.BytesIO(b""), "image/png"))],
        timeout=10,
    )
    all_passed &= assert_status("Reject empty file -> 400", r_empty, 400)

    # 7c: non-existent inspection
    r_no_insp = httpx.post(
        f"{base}/api/v1/inspections/999999/images",
        files=[("files", ("x.png", io.BytesIO(png_bytes), "image/png"))],
        timeout=10,
    )
    all_passed &= assert_status("Upload to missing inspection -> 404", r_no_insp, 404)

    # 7d: list images for non-existent inspection
    r_list_404 = httpx.get(f"{base}/api/v1/inspections/999999/images", timeout=10)
    all_passed &= assert_status("List images missing inspection -> 404", r_list_404, 404)

    # ── 8. Delete image ──────────────────────────────────────────────────
    print("\n[8] DELETE /inspections/{id}/images/{image_id}")
    r_del = httpx.delete(
        f"{base}/api/v1/inspections/{inspection_id}/images/{image_id}",
        timeout=10,
    )
    all_passed &= assert_status("Delete image", r_del, 200)
    del_body = r_del.json()
    all_passed &= assert_eq("  response id matches", del_body["id"], image_id)

    # ── 9. Verify DB record gone ─────────────────────────────────────────
    print("\n[9] Verify DB record and physical file removed")
    r_imgs_after = httpx.get(f"{base}/api/v1/inspections/{inspection_id}/images", timeout=10)
    if r_imgs_after.status_code == 200:
        still_there = any(img["id"] == image_id for img in r_imgs_after.json())
        if not still_there:
            ok("  DB record absent after delete")
        else:
            fail("  DB record still present after delete")
            all_passed = False
    else:
        fail("  Could not list images after delete", str(r_imgs_after.status_code))
        all_passed = False

    # Verify file gone
    if not os.path.exists(abs_path):
        ok(f"  Physical file removed: {abs_path}")
    else:
        fail("  Physical file still exists after delete")
        all_passed = False

    # ── 10. Delete wrong inspection/image combo -> 404 ───────────────────
    print("\n[10] Delete image from wrong inspection -> 404")
    r_del_wrong = httpx.delete(
        f"{base}/api/v1/inspections/999999/images/{image_id}",
        timeout=10,
    )
    all_passed &= assert_status("Delete from wrong inspection -> 404", r_del_wrong, 404)

    # ── 11. Cleanup: delete test inspection ──────────────────────────────
    print("\n[11] Cleanup test inspection")
    r_cleanup = httpx.delete(f"{base}/api/v1/inspections/{inspection_id}", timeout=10)
    all_passed &= assert_status("Delete test inspection", r_cleanup, 200)

    return all_passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("STEP 5 - IMAGE UPLOAD INTEGRATION TEST")
    print("=" * 55)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8008"],
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

"""
Integration test for database persistence in /api/v1/inspect.
Tests that single-shot inspections correctly write records to SQLite.
"""

import os
import sys
from pathlib import Path

# Setup paths
repo_root = Path(__file__).resolve().parent.parent
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(repo_root / "ai-engine"))
sys.path.insert(0, str(repo_root / "rules-engine" / "legal-core"))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, init_db
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.declaration import Declaration
from app.models.violation import Violation
from app.models.product import Product

def test_inspect_persistence():
    print("\n--- Initializing DB ---")
    init_db()

    client = TestClient(app)

    from PIL import Image
    import io

    # Create valid 100x100 RGB image
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_png_bytes = buf.getvalue()

    files = {
        "front_image": ("front_sample.png", valid_png_bytes, "image/png"),
        "back_image": ("back_sample.png", valid_png_bytes, "image/png"),
    }
    data = {
        "demo_mode": "true",
        "use_rag": "false",
    }

    print("--- POST /api/v1/inspect (demo_mode=true) ---")
    response = client.post("/api/v1/inspect", files=files, data=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    resp_data = response.json()
    print("Response status:", resp_data.get("status"))
    print("Response inspection_id:", resp_data.get("inspection_id"))
    print("Response reference_number:", resp_data.get("reference_number"))

    db_id = resp_data.get("inspection_id")
    assert db_id is not None, "inspection_id missing in response"

    # Verify SQLite DB records
    with SessionLocal() as db:
        insp = db.get(Inspection, db_id)
        assert insp is not None, f"Inspection {db_id} not found in database"
        print(f"Verified Inspection record in DB: id={insp.id}, status={insp.status}, score={insp.compliance_score}")

        images = db.query(InspectionImage).filter(InspectionImage.inspection_id == db_id).all()
        print(f"Verified InspectionImage records: count={len(images)}")
        assert len(images) >= 2, "Expected at least 2 inspection image records"

        decls = db.query(Declaration).filter(Declaration.inspection_id == db_id).all()
        print(f"Verified Declaration records: count={len(decls)}")
        assert len(decls) > 0, "Expected declaration records in DB"

        violations = db.query(Violation).filter(Violation.inspection_id == db_id).all()
        print(f"Verified Violation records: count={len(violations)}")

        if insp.product_id:
            prod = db.get(Product, insp.product_id)
            print(f"Verified linked Product in DB: {prod.name} (id={prod.id})")

    # Verify GET /api/v1/inspections list contains this inspection
    print("--- GET /api/v1/inspections ---")
    list_resp = client.get("/api/v1/inspections")
    assert list_resp.status_code == 200
    list_items = list_resp.json()
    found = any(item.get("id") == db_id for item in list_items)
    assert found, f"Inspection id {db_id} not found in list_inspections response"
    print("Verified inspection present in /api/v1/inspections listing!")

    print("\nALL DATABASE INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_inspect_persistence()

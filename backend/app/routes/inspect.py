"""
Single-shot Inspection Endpoint.
Accepts product packaging images (front, back, and optional side),
runs the end-to-end AI/OCR fact extraction and legal metrology compliance rules engine,
and returns a structured result ready for the frontend.
"""

import os
import sys
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Ensure repo root, ai-engine, and rules-engine/legal-core are on sys.path
_current_dir = Path(__file__).resolve().parent
_repo_root = _current_dir.parents[2]

for _path in [
    str(_repo_root),
    str(_repo_root / "ai-engine"),
    str(_repo_root / "rules-engine" / "legal-core"),
]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from integration.orchestrator import run_full_inspection
from app.database import get_db
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.declaration import Declaration
from app.models.violation import Violation
from app.models.product import Product
from app.routes.images import UPLOADS_DIR

router = APIRouter(prefix="/api/v1", tags=["Inspect"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _validate_image_file(file: UploadFile) -> str:
    """Validate file presence and extension, returning file extension."""
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename."
        )
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


@router.post(
    "/inspect",
    status_code=status.HTTP_200_OK,
    summary="Run full end-to-end inspection pipeline (AI/OCR -> Compliance)",
)
async def inspect_product(
    front_image: UploadFile = File(..., description="Front view label image"),
    back_image: UploadFile = File(..., description="Back view label image"),
    side_image: Optional[UploadFile] = File(None, description="Optional side view label image"),
    demo_mode: bool = Form(False, description="Use demo sample fallbacks if true"),
    use_rag: bool = Form(False, description="Enable legal citation RAG search if true"),
    db: Session = Depends(get_db),
):
    """
    Accepts multipart packaging images, runs OCR and legal rules validation,
    persists records to SQLite DB, and returns a unified inspection result.
    """
    start_time = time.time()
    
    # Validate image files
    front_ext = _validate_image_file(front_image)
    back_ext = _validate_image_file(back_image)
    side_ext = _validate_image_file(side_image) if (side_image and side_image.filename) else None

    # Ensure uploads directory exists
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Create initial inspection record in SQLite database
    ref_number = f"INSP-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    inspection = Inspection(
        reference_number=ref_number,
        status="processing",
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    try:
        # Save front image permanently to uploads/
        front_filename = f"inspection_{inspection.id}_{uuid.uuid4().hex}{front_ext}"
        front_path = UPLOADS_DIR / front_filename
        with open(front_path, "wb") as f_out:
            shutil.copyfileobj(front_image.file, f_out)

        db.add(InspectionImage(
            inspection_id=inspection.id,
            file_path=f"uploads/{front_filename}",
            panel_type="front",
        ))

        # Save back image permanently to uploads/
        back_filename = f"inspection_{inspection.id}_{uuid.uuid4().hex}{back_ext}"
        back_path = UPLOADS_DIR / back_filename
        with open(back_path, "wb") as f_out:
            shutil.copyfileobj(back_image.file, f_out)

        db.add(InspectionImage(
            inspection_id=inspection.id,
            file_path=f"uploads/{back_filename}",
            panel_type="back",
        ))

        # Save side image permanently to uploads/ if present
        side_path = None
        if side_image and side_image.filename and side_ext:
            side_filename = f"inspection_{inspection.id}_{uuid.uuid4().hex}{side_ext}"
            side_path = UPLOADS_DIR / side_filename
            with open(side_path, "wb") as f_out:
                shutil.copyfileobj(side_image.file, f_out)

            db.add(InspectionImage(
                inspection_id=inspection.id,
                file_path=f"uploads/{side_filename}",
                panel_type="side",
            ))

        db.commit()

        # Run pipeline via integration orchestrator using persistent file paths
        result = run_full_inspection(
            front_path=str(front_path.resolve()),
            back_path=str(back_path.resolve()),
            side_path=str(side_path.resolve()) if side_path else None,
            demo_mode=demo_mode,
            use_rag=use_rag,
        )

    except Exception as exc:
        inspection.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inspection pipeline execution error: {str(exc)}"
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inspection pipeline returned no result."
        )

    ai_result = result.get("ai_result") or {}
    if not ai_result.get("success", False):
        errors = ai_result.get("errors", ["OCR extraction failed"])
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "AI/OCR extraction failed", "errors": errors}
        )

    compliance = result.get("compliance_result") or {}
    detections = ai_result.get("detections", [])

    # Map overall status
    raw_status = compliance.get("overall_status", "REVIEW")
    status_map = {
        "PASS": "COMPLIANT",
        "FAIL": "VIOLATION",
        "REVIEW": "REVIEW_REQUIRED",
    }
    mapped_status = status_map.get(raw_status, "REVIEW_REQUIRED")

    # Field alias map for frontend ease of access
    field_alias_map = {
        "product_name": "productName",
        "manufacturer_packer_importer": "manufacturer",
        "net_quantity": "netQuantity",
        "mrp": "mrp",
        "manufacturing_date": "packedDate",
        "best_before": "bestBefore",
        "consumer_care": "consumerCare",
        "country_of_origin": "countryOfOrigin",
        "unit_sale_price": "unitSalePrice",
    }

    # Format extracted data and OCR confidence
    extracted_data: Dict[str, Any] = {}
    ocr_confidence: Dict[str, float] = {}

    for det in detections:
        f_name = det.get("field")
        val = det.get("value")
        raw_conf = det.get("confidence", 0.0) or 0.0
        conf_pct = round(raw_conf * 100) if raw_conf <= 1.0 else round(raw_conf)
        item = {
            "value": val,
            "confidence": conf_pct,
            "status": det.get("status", "found" if val else "not_found"),
            "source": det.get("source_image", "front/back"),
        }
        extracted_data[f_name] = item
        ocr_confidence[f_name] = round(raw_conf, 4)

        # Also store camelCase aliases
        if f_name in field_alias_map:
            alias = field_alias_map[f_name]
            extracted_data[alias] = item
            ocr_confidence[alias] = round(raw_conf, 4)

    # Top-level convenient attributes
    product_title = (
        extracted_data.get("product_name", {}).get("value")
        or extracted_data.get("productName", {}).get("value")
        or "Packaged Commodity Item"
    )
    manufacturer_val = (
        extracted_data.get("manufacturer_packer_importer", {}).get("value")
        or extracted_data.get("manufacturer", {}).get("value")
        or ""
    )
    net_qty_val = (
        extracted_data.get("net_quantity", {}).get("value")
        or extracted_data.get("netQuantity", {}).get("value")
        or ""
    )
    mrp_val = extracted_data.get("mrp", {}).get("value") or ""
    usp_val = extracted_data.get("unit_sale_price", {}).get("value") or ""
    packed_date_val = extracted_data.get("manufacturing_date", {}).get("value") or ""
    best_before_val = extracted_data.get("best_before", {}).get("value") or ""
    consumer_care_val = extracted_data.get("consumer_care", {}).get("value") or ""
    country_of_origin_val = extracted_data.get("country_of_origin", {}).get("value") or "India"

    # Map checks and violations
    checks: List[Dict[str, Any]] = []
    violations: List[Dict[str, Any]] = []

    for chk in compliance.get("checks", []):
        chk_id = chk.get("check_id") or "CHK-00"
        rule_name = chk.get("rule_name") or "Mandatory Declaration Check"
        legal_src = chk.get("legal_source") or {}
        rule_ref = legal_src.get("rule") or rule_name
        chk_status = chk.get("status", "REVIEW")
        conf = chk.get("confidence") or 0.90
        det_val = chk.get("detected_value") or "Not Found"
        exp_val = chk.get("expected") or "Mandatory declaration under Legal Metrology Rules"
        reason = chk.get("reason") or ""
        severity = chk.get("severity") or "MEDIUM"

        check_obj = {
            "id": chk_id,
            "name": rule_name,
            "ruleRef": rule_ref,
            "status": chk_status,
            "confidence": conf,
            "detectedValue": det_val,
            "expectedRequirement": exp_val,
            "explanation": reason,
            "severity": severity,
            "evidence": chk.get("evidence", ""),
        }
        checks.append(check_obj)

        if chk_status == "FAIL":
            violations.append({
                "id": f"VIOL-{chk_id}",
                "title": f"{rule_name} Non-Compliance",
                "ruleRef": rule_ref,
                "severity": severity,
                "detectedValue": det_val,
                "expectedRequirement": exp_val,
                "explanation": reason,
                "confidence": conf,
                "recommendedAction": "Direct manufacturer/packer to issue corrective declaration before sale under Legal Metrology Rules.",
            })

    # Bounding boxes
    bounding_boxes: List[Dict[str, Any]] = []
    for det in detections:
        raw_bbox = det.get("bbox")
        if raw_bbox and len(raw_bbox) >= 4 and det.get("status") in ("found", "low_confidence"):
            try:
                xs = [pt[0] for pt in raw_bbox]
                ys = [pt[1] for pt in raw_bbox]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                bounding_boxes.append({
                    "field": det.get("label", det.get("field")),
                    "value": det.get("value"),
                    "confidence": round((det.get("confidence", 0) or 0) * 100),
                    "x": round(min_x, 1),
                    "y": round(min_y, 1),
                    "width": round(max_x - min_x, 1),
                    "height": round(max_y - min_y, 1),
                    "source_image": det.get("source_image"),
                })
            except Exception:
                pass

    # 2. Persist Declarations to DB
    for det in detections:
        f_name = det.get("field")
        val = det.get("value")
        raw_conf = det.get("confidence", 0.0) or 0.0
        if f_name:
            decl = Declaration(
                inspection_id=inspection.id,
                field_name=f_name,
                value=str(val) if val is not None else None,
                confidence=round(raw_conf, 4) if raw_conf else None,
                status="extracted" if val else "missing",
            )
            db.add(decl)

    # 3. Create and link Product record if title exists
    if product_title and product_title != "Packaged Commodity Item":
        prod = Product(
            name=product_title,
            manufacturer=manufacturer_val or None,
        )
        db.add(prod)
        db.flush()
        inspection.product_id = prod.id

    # 4. Persist Violations to DB
    for chk in compliance.get("checks", []):
        if chk.get("status") == "FAIL":
            chk_id = chk.get("check_id") or "CHK"
            rule_name = chk.get("rule_name") or "Mandatory Declaration Check"
            reason = chk.get("reason") or rule_name
            db.add(Violation(
                inspection_id=inspection.id,
                rule_id=None,
                field_name=chk.get("field"),
                severity=(chk.get("severity") or "medium").lower(),
                description=f"[{chk_id}] {reason}",
                confidence=chk.get("confidence"),
                status="open",
            ))

    # 5. Update and finalize Inspection record
    total_time_ms = round((time.time() - start_time) * 1000)
    score = round(compliance.get("automated_check_score", 0.0), 1)

    inspection.compliance_score = score
    if mapped_status == "COMPLIANT":
        inspection.status = "compliant"
    elif mapped_status == "VIOLATION":
        inspection.status = "non_compliant"
    else:
        inspection.status = "completed"

    db.commit()
    db.refresh(inspection)

    return {
        "id": ref_number,
        "inspection_id": inspection.id,
        "reference_number": ref_number,
        "db_id": inspection.id,
        "status": mapped_status,
        "score": score,
        "confidence": 0.95,
        "product": product_title,
        "productName": product_title,
        "manufacturer": manufacturer_val,
        "netQuantity": net_qty_val,
        "mrp": mrp_val,
        "unitSalePrice": usp_val,
        "packedDate": packed_date_val,
        "bestBefore": best_before_val,
        "consumerCare": consumer_care_val,
        "countryOfOrigin": country_of_origin_val,
        "processingTimeMs": total_time_ms,
        "extractedData": extracted_data,
        "ocrConfidence": ocr_confidence,
        "checks": checks,
        "complianceChecks": checks,
        "violations": violations,
        "boundingBoxes": bounding_boxes,
        "disclaimers": compliance.get("disclaimers", [
            "AI-assisted preliminary assessment under Legal Metrology (Packaged Commodities) Rules, 2011. Final verification by authorized inspector recommended."
        ]),
        "summary": compliance.get("summary", {}),
        "rawResult": {
            "ai": ai_result.get("metadata", {}),
            "structuredFacts": result.get("structured_facts"),
        }
    }


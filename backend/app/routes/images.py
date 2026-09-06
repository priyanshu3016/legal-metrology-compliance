"""
APIRouter: Inspection Images

Prefix : /api/v1/inspections/{inspection_id}/images
Tags   : ["Inspection Images"]

Endpoints
---------
POST   /          Upload one or more label images for an inspection
GET    /          List all images for an inspection
DELETE /{image_id} Delete an image record and its physical file

Security / robustness
---------------------
- Filenames are NEVER used as-is from the client. A UUID-based name is generated.
- File extension is validated against ALLOWED_EXTENSIONS whitelist.
- Content-type header is checked as a secondary signal.
- Empty uploads are rejected (400).
- File size is limited to MAX_FILE_BYTES (10 MB) per file.
- Path traversal is impossible because the storage path is constructed
  entirely from server-side values (uuid + sanitised extension).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.schemas.image import ImageDeleteResponse, ImageRead, ImageUploadResponse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}
ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_FILE_BYTES: int = 10 * 1024 * 1024  # 10 MB per file

# Resolved at import time; main.py guarantees the directory exists.
UPLOADS_DIR: Path = Path(__file__).resolve().parents[2] / "uploads"

router = APIRouter(
    prefix="/api/v1/inspections/{inspection_id}/images",
    tags=["Inspection Images"],
)

# ---------------------------------------------------------------------------
# Dependency alias
# ---------------------------------------------------------------------------
DBSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_inspection_or_404(inspection_id: int, db: Session) -> Inspection:
    obj = db.get(Inspection, inspection_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with id={inspection_id} not found.",
        )
    return obj


def _get_image_or_404(
    image_id: int, inspection_id: int, db: Session
) -> InspectionImage:
    img = db.get(InspectionImage, image_id)
    if img is None or img.inspection_id != inspection_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Image with id={image_id} not found "
                f"for inspection id={inspection_id}."
            ),
        )
    return img


def _validate_file(file: UploadFile) -> str:
    """
    Validate a single UploadFile and return the safe lowercase extension.

    Raises HTTP 400 on:
      - missing / empty filename
      - disallowed extension
      - disallowed content-type
      - zero-length file
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file has no filename.",
        )

    # Extension check (never trust just content-type)
    original_name = Path(file.filename).name          # strip any path components
    ext = Path(original_name).suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '.{ext}' is not allowed. "
                f"Accepted types: {sorted(ALLOWED_EXTENSIONS)}"
            ),
        )

    # Content-type check
    ct = (file.content_type or "").lower()
    if ct and ct not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Content-type '{ct}' is not accepted. "
                f"Expected one of: {sorted(ALLOWED_CONTENT_TYPES)}"
            ),
        )

    return ext


def _save_file(inspection_id: int, ext: str, data: bytes) -> str:
    """
    Write *data* to the uploads directory using a UUID filename.
    Returns the relative path stored in the database (relative to backend/).
    """
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File exceeds the maximum allowed size of "
                f"{MAX_FILE_BYTES // (1024 * 1024)} MB."
            ),
        )

    filename = f"inspection_{inspection_id}_{uuid.uuid4().hex}.{ext}"
    dest = UPLOADS_DIR / filename
    dest.write_bytes(data)

    # Store path relative to backend/ so it is portable
    return f"uploads/{filename}"


# ---------------------------------------------------------------------------
# POST /api/v1/inspections/{inspection_id}/images  — Upload
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload label images for an inspection",
    description=(
        "Upload one or more product/package label images (JPG, JPEG, PNG, WebP). "
        "Files are stored in `backend/uploads/` with UUID-based filenames. "
        "Metadata is saved in the `inspection_images` table. "
        "Maximum file size: **10 MB per image**."
    ),
)
def upload_images(
    inspection_id: int,
    db: DBSession,
    files: List[UploadFile] = File(
        ...,
        description="One or more image files (jpg/jpeg/png/webp)",
    ),
    panel_type: str | None = Form(
        default=None,
        description=(
            "Optional label panel identifier, e.g. 'front', 'back', 'side'. "
            "Applied to all files in this upload batch."
        ),
    ),
) -> ImageUploadResponse:
    _get_inspection_or_404(inspection_id, db)

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were supplied.",
        )

    saved: list[InspectionImage] = []
    for file in files:
        ext = _validate_file(file)
        data = file.file.read()
        rel_path = _save_file(inspection_id, ext, data)

        record = InspectionImage(
            inspection_id=inspection_id,
            file_path=rel_path,
            panel_type=panel_type,
        )
        db.add(record)
        db.flush()   # get the generated id without committing yet
        saved.append(record)

    db.commit()
    for rec in saved:
        db.refresh(rec)

    return ImageUploadResponse(
        uploaded=len(saved),
        images=saved,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/inspections/{inspection_id}/images  — List
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[ImageRead],
    summary="List images for an inspection",
    description="Return all images uploaded for the specified inspection.",
)
def list_images(
    inspection_id: int,
    db: DBSession,
) -> list[InspectionImage]:
    _get_inspection_or_404(inspection_id, db)
    return (
        db.query(InspectionImage)
        .filter(InspectionImage.inspection_id == inspection_id)
        .order_by(InspectionImage.uploaded_at.asc())
        .all()
    )


# ---------------------------------------------------------------------------
# DELETE /api/v1/inspections/{inspection_id}/images/{image_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{image_id}",
    response_model=ImageDeleteResponse,
    summary="Delete an inspection image",
    description=(
        "Delete an image record from the database **and** the physical file "
        "from disk. Only succeeds if the image belongs to the specified inspection."
    ),
)
def delete_image(
    inspection_id: int,
    image_id: int,
    db: DBSession,
) -> ImageDeleteResponse:
    _get_inspection_or_404(inspection_id, db)
    img = _get_image_or_404(image_id, inspection_id, db)

    # Resolve absolute path and delete if present
    abs_path = (UPLOADS_DIR.parent / img.file_path).resolve()
    # Safety: ensure resolved path is still under uploads/
    try:
        abs_path.relative_to(UPLOADS_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refusing to delete file outside the uploads directory.",
        )

    file_deleted = False
    if abs_path.exists():
        abs_path.unlink()
        file_deleted = True

    db.delete(img)
    db.commit()

    return ImageDeleteResponse(
        message=(
            f"Image id={image_id} deleted from database"
            f"{' and disk' if file_deleted else ' (file was already absent from disk)'}."
        ),
        id=image_id,
    )

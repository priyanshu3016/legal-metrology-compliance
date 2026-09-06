"""
Report generation service — app/services/report.py

Generates a PDF compliance inspection report using ReportLab.

Architecture
------------
  Inspection + Declarations + Violations + Evidence
          |
  generate_pdf()   <-- pure PDF generation, no compliance logic
          |
  PDF file saved to reports/
  SHA-256 hash computed
  File path + hash returned to caller

The caller (route handler) persists the Report ORM record.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Directory setup (resolved relative to this file's location)
# ---------------------------------------------------------------------------
REPORTS_DIR: Path = Path(__file__).resolve().parents[2] / "reports"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _fmt(value: Any) -> str:
    """Return a displayable string or a dash for missing values."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return "—"
    return str(value)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_pdf(
    *,
    inspection_id: int,
    reference_number: str,
    location: str | None,
    inspector_name: str | None,
    inspection_date: datetime,
    declarations: dict[str, str | None],
    overall_status: str,
    compliance_score: float | None,
    total_checks: int,
    passed_checks: int,
    failed_checks: int,
    violations: list[dict],        # list of {field_name, severity, description}
    evidence: list[dict],          # list of {description, field_name, confidence}
) -> tuple[Path, str]:
    """
    Generate a PDF report and save it to REPORTS_DIR.

    Returns
    -------
    (abs_path, sha256_hex)
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"report_{inspection_id}_{uuid.uuid4().hex[:8]}.pdf"
    dest = REPORTS_DIR / filename

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=14,
        spaceAfter=6,
        textColor=colors.HexColor("#1a237e"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#283593"),
        spaceBefore=12,
        spaceAfter=4,
    )
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=8, textColor=colors.grey)

    doc = SimpleDocTemplate(
        str(dest),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    # ── Title ─────────────────────────────────────────────────────────────
    story.append(Paragraph("LEGAL METROLOGY COMPLIANCE INSPECTION REPORT", title_style))
    story.append(Paragraph("Government of India — Department for Promotion of Industry and Internal Trade", small))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
    story.append(Spacer(1, 0.3 * cm))

    # ── Inspection details ────────────────────────────────────────────────
    story.append(Paragraph("Inspection Details", heading_style))
    insp_data = [
        ["Reference Number", _fmt(reference_number)],
        ["Inspection Date", inspection_date.strftime("%d %B %Y, %H:%M UTC")],
        ["Location", _fmt(location)],
        ["Inspector", _fmt(inspector_name)],
    ]
    insp_table = Table(insp_data, colWidths=[5 * cm, 12 * cm])
    insp_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND",  (0, 0), (0, -1), colors.HexColor("#e8eaf6")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#bdbdbd")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(insp_table)

    # ── Label declarations ────────────────────────────────────────────────
    story.append(Paragraph("Label Declarations", heading_style))
    label_fields = [
        ("Product Name",             declarations.get("product_name")),
        ("Manufacturer/Packer",      declarations.get("manufacturer")),
        ("Net Quantity",             declarations.get("net_quantity")),
        ("MRP",                      declarations.get("mrp")),
        ("Date of Manufacturing",    declarations.get("date_of_manufacturing")),
        ("Date of Packing",          declarations.get("date_of_packing")),
        ("Best Before / Use By",     declarations.get("best_before") or declarations.get("use_by")),
        ("Consumer Care",            declarations.get("consumer_care")),
        ("Country of Origin",        declarations.get("country_of_origin")),
        ("Unit Sale Price",          declarations.get("unit_sale_price")),
        ("Brand",                    declarations.get("brand")),
        ("Importer",                 declarations.get("importer")),
    ]
    decl_data = [["Field", "Declared Value"]] + [
        [label, _fmt(value)] for label, value in label_fields
    ]
    decl_table = Table(decl_data, colWidths=[5 * cm, 12 * cm])
    decl_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#283593")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 1), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND",  (0, 1), (0, -1), colors.HexColor("#e8eaf6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#bdbdbd")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(decl_table)

    # ── Compliance summary ────────────────────────────────────────────────
    story.append(Paragraph("Compliance Summary", heading_style))
    status_color = colors.HexColor("#1b5e20") if overall_status == "COMPLIANT" else colors.HexColor("#b71c1c")
    summary_data = [
        ["Overall Status",   overall_status],
        ["Compliance Score", f"{_fmt(compliance_score)}%"],
        ["Total Checks",     str(total_checks)],
        ["Passed Checks",    str(passed_checks)],
        ["Failed Checks",    str(failed_checks)],
    ]
    sum_table = Table(summary_data, colWidths=[5 * cm, 12 * cm])
    sum_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND",  (0, 0), (0, -1), colors.HexColor("#e8eaf6")),
        ("TEXTCOLOR",   (1, 0), (1, 0), status_color),
        ("FONTNAME",    (1, 0), (1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#bdbdbd")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sum_table)

    # ── Violations ────────────────────────────────────────────────────────
    story.append(Paragraph("Violations", heading_style))
    if violations:
        viol_data = [["Field", "Severity", "Description"]] + [
            [
                _fmt(v.get("field_name")),
                v.get("severity", "").upper(),
                _fmt(v.get("description")),
            ]
            for v in violations
        ]
        viol_table = Table(viol_data, colWidths=[4 * cm, 2.5 * cm, 10.5 * cm])
        viol_table.setStyle(TableStyle([
            ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#b71c1c")),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ffebee")]),
            ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#bdbdbd")),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("WORDWRAP",    (2, 1), (2, -1), True),
        ]))
        story.append(viol_table)
    else:
        story.append(Paragraph("No violations detected.", normal))

    # ── Evidence ──────────────────────────────────────────────────────────
    story.append(Paragraph("Evidence", heading_style))
    if evidence:
        ev_data = [["Description", "Field", "Confidence"]] + [
            [
                _fmt(e.get("description")),
                _fmt(e.get("field_name")),
                f"{e['confidence']:.2f}" if e.get("confidence") is not None else "—",
            ]
            for e in evidence
        ]
        ev_table = Table(ev_data, colWidths=[9 * cm, 4 * cm, 4 * cm])
        ev_table.setStyle(TableStyle([
            ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e8eaf6")]),
            ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#bdbdbd")),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ev_table)
    else:
        story.append(Paragraph("No evidence records.", normal))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    sha_placeholder = "Computing..."  # will be replaced after build
    story.append(Paragraph(f"Report generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", small))
    story.append(Paragraph("This is a prototype inspection report. It is NOT a legally certified document.", small))

    doc.build(story)

    sha = _sha256(dest)
    return dest, sha

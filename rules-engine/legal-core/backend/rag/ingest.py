"""
RAG Ingestion Engine for Legal Metrology (Packaged Commodities) Compliance.

Extracts, cleans, and segments:
  - rules2009.pdf (The Legal Metrology Act, 2009)
  - rules2011.pdf (The Legal Metrology (Packaged Commodities) Rules, 2011)

Produces rule-aware, context-preserving legal chunks with metadata
conforming to MVP_BUILD_SPEC.md and MASTER_BUILD_SPEC.md.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from backend.rag.schemas import LegalChunk, ChunkMetadata


# Document Titles
DOC_TITLES = {
    "rules2011.pdf": "The Legal Metrology (Packaged Commodities) Rules, 2011",
    "rules2009.pdf": "The Legal Metrology Act, 2009"
}


def clean_pdf_text(text: str) -> str:
    """
    Clean extracted PDF text:
    - Removes running header/footers ('Page X of 43', standalone numbers)
    - Fixes OCR replacement characters and non-breaking spaces
    - Standardizes quotes and dashes
    - Normalizes multi-space indentation while preserving paragraph breaks
    """
    # Remove running footer like 'Page 5 of 43'
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    # Remove standalone page numbers on new lines
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    # Normalize unicode whitespace & characters
    text = text.replace('\xa0', ' ')
    text = text.replace('\u2013', '-').replace('\u2014', '-')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\ufffd', '-')
    # Normalize consecutive spaces and excessive newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()


def extract_pages_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text from each PDF page preserving 1-indexed page numbers.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Source PDF file not found at: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    pages = []
    for idx, page in enumerate(doc):
        raw_text = page.get_text("text")
        cleaned_text = clean_pdf_text(raw_text)
        pages.append({
            "page_number": idx + 1,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text
        })
    doc.close()
    return pages


def resolve_pdf_paths(base_dir: Optional[str] = None) -> Tuple[str, str]:
    """
    Locates rules2009.pdf and rules2011.pdf strictly in the canonical legal_docs/ directory.
    Checks:
    1. base_dir/legal_docs/
    2. Parent directories outward: parent/legal_docs/
    3. Workspace root relative to this file: backend/rag/../../legal_docs/
    """
    if base_dir is None:
        base_dir = os.getcwd()

    # Search outward for canonical legal_docs directory
    search_dirs = [
        os.path.abspath(base_dir),
        os.path.abspath(os.path.join(base_dir, "..")),
        os.path.abspath(os.path.join(base_dir, "..", "..")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
    ]

    candidates_2009 = [os.path.join(d, "legal_docs", "rules2009.pdf") for d in search_dirs]
    candidates_2011 = [os.path.join(d, "legal_docs", "rules2011.pdf") for d in search_dirs]

    path_2009 = next((p for p in candidates_2009 if os.path.exists(p)), None)
    path_2011 = next((p for p in candidates_2011 if os.path.exists(p)), None)

    if not path_2009 or not path_2011:
        raise FileNotFoundError(
            f"Could not locate legal PDFs in legal_docs/. Found 2009: {path_2009}, 2011: {path_2011} "
            f"under base directory: {base_dir}"
        )

    return path_2009, path_2011


def chunk_rules2011(pages: List[Dict[str, Any]]) -> List[LegalChunk]:
    """
    Produces rule-aware chunks for the 2011 Packaged Commodities Rules.
    Performs specialized fine-grained sub-rule splitting on:
      - Rule 2 (Definitions: retail sale price, manufacturer, packer, retail package)
      - Rule 6 (Mandatory declarations: 6(1)(a)-(g), 6(2) consumer care, 6(3) stickers, etc.)
      - Rule 12 (Quantity manner, specifically 12(6) misleading qualifiers)
    """
    doc_name = "rules2011.pdf"
    doc_title = DOC_TITLES[doc_name]
    chunks: List[LegalChunk] = []

    # Map lines with source page numbers
    lines_with_pages: List[Tuple[str, int]] = []
    for p in pages:
        p_num = p["page_number"]
        for line in p["cleaned_text"].split("\n"):
            line_str = line.strip()
            if line_str:
                lines_with_pages.append((line_str, p_num))

    # Identify structural boundaries
    rule_headers = []
    for idx, (line, p_num) in enumerate(lines_with_pages):
        # Match Schedules
        sched_m = re.match(r'^(?:THE\s+)?([A-Z]+)\s+SCHEDULE', line, re.IGNORECASE)
        if sched_m:
            sched_name = sched_m.group(1).upper()
            rule_headers.append({
                "idx": idx,
                "type": "schedule",
                "schedule": sched_name,
                "rule_num": None,
                "title": f"The {sched_name.capitalize()} Schedule",
                "page": p_num
            })
            continue

        # Match Rules
        rule_m = re.match(r'^(\d+)\.\s+([^\n]+)', line)
        if rule_m:
            num = int(rule_m.group(1))
            # Rules 1-34 appear on pages <= 28
            if num <= 34 and p_num <= 28:
                rule_headers.append({
                    "idx": idx,
                    "type": "rule",
                    "schedule": None,
                    "rule_num": str(num),
                    "title": rule_m.group(2).strip().rstrip(".-–—: "),
                    "page": p_num
                })

    rule_headers.sort(key=lambda x: x["idx"])

    def get_2011_chapter(page_no: int) -> str:
        if page_no < 4:
            return "I"
        elif page_no < 23:
            return "II"
        elif page_no < 24:
            return "III"
        elif page_no < 25:
            return "IV"
        elif page_no < 27:
            return "VI"
        elif page_no < 28:
            return "VII"
        else:
            return "SCHEDULES"

    for h_idx, h in enumerate(rule_headers):
        start_line = h["idx"]
        end_line = rule_headers[h_idx + 1]["idx"] if h_idx + 1 < len(rule_headers) else len(lines_with_pages)
        rule_lines = lines_with_pages[start_line:end_line]
        start_page = h["page"]
        chapter = get_2011_chapter(start_page)

        # Rule 6: Mandatory retail label declarations
        if h["rule_num"] == "6":
            rule6_chunks = _split_rule6(rule_lines, doc_name, doc_title, chapter)
            chunks.extend(rule6_chunks)
        # Rule 2: Definitions
        elif h["rule_num"] == "2":
            rule2_chunks = _split_rule2(rule_lines, doc_name, doc_title, chapter)
            chunks.extend(rule2_chunks)
        # Rule 12: Manner of quantity declaration
        elif h["rule_num"] == "12":
            rule12_chunks = _split_rule12(rule_lines, doc_name, doc_title, chapter)
            chunks.extend(rule12_chunks)
        else:
            # Standard Rule or Schedule
            c_type = "schedule" if h["type"] == "schedule" else "rule"
            if h["type"] == "schedule":
                c_id = f"rules2011_sched_{h['schedule'].lower()}"
                citation = f"The {h['schedule'].capitalize()} Schedule, {doc_title} (Page {start_page})"
            else:
                c_id = f"rules2011_rule{h['rule_num']}"
                citation = f"Rule {h['rule_num']}, {doc_title} (Page {start_page})"

            rule_text = "\n".join(l[0] for l in rule_lines)
            context_header = f"[{doc_title} | Chapter {chapter} | {h['title']}]"
            full_text = f"{context_header}\n{rule_text}"

            metadata = ChunkMetadata(
                document=doc_name,
                document_name=doc_name,
                document_title=doc_title,
                rule=h["rule_num"],
                rule_number=h["rule_num"],
                sub_rule=None,
                clause=None,
                chapter=chapter,
                page=start_page,
                page_number=start_page,
                chunk_type=c_type,
                title=h["title"],
                section_title=h["title"],
                citation=citation
            )
            chunks.append(LegalChunk(chunk_id=c_id, text=full_text, metadata=metadata))

    return chunks


def _split_rule2(lines_with_pages: List[Tuple[str, int]], doc_name: str, doc_title: str, chapter: str) -> List[LegalChunk]:
    """Splits Rule 2 definitions into individual definition chunks."""
    chunks = []
    clause_pattern = re.compile(
        r'^\(([a-z]+)\)\s+[\'\"`\u2018\u201c]?([a-zA-Z\s]+)[\'\"`\u2019\u201d]?\s*(?:means|in relation to|,|\b)',
        re.IGNORECASE
    )
    parent_ctx = f"[{doc_title} | Chapter I: Preliminary | Rule 2: Definitions]"

    current_clause = None
    current_term = None
    clause_lines = []
    start_page = 1

    for line, page in lines_with_pages:
        m = clause_pattern.match(line)
        if m:
            if current_clause and clause_lines:
                c_text = "\n".join(clause_lines)
                c_title = f"Definition of '{current_term}'"
                c_id = f"rules2011_rule2_{current_clause}"
                citation = f"Rule 2({current_clause}), {doc_title} (Page {start_page})"
                meta = ChunkMetadata(
                    document=doc_name,
                    document_name=doc_name,
                    document_title=doc_title,
                    rule="2",
                    rule_number="2",
                    sub_rule=None,
                    clause=current_clause,
                    chapter=chapter,
                    page=start_page,
                    page_number=start_page,
                    chunk_type="definition",
                    title=c_title,
                    section_title="Definitions",
                    citation=citation
                )
                chunks.append(LegalChunk(
                    chunk_id=c_id,
                    text=f"{parent_ctx} | Clause ({current_clause}) '{current_term}':\n{c_text}",
                    metadata=meta
                ))
            current_clause = m.group(1).lower()
            current_term = m.group(2).strip()
            clause_lines = [line]
            start_page = page
        else:
            clause_lines.append(line)

    if current_clause and clause_lines:
        c_text = "\n".join(clause_lines)
        c_title = f"Definition of '{current_term}'"
        c_id = f"rules2011_rule2_{current_clause}"
        citation = f"Rule 2({current_clause}), {doc_title} (Page {start_page})"
        meta = ChunkMetadata(
            document=doc_name,
            document_name=doc_name,
            document_title=doc_title,
            rule="2",
            rule_number="2",
            sub_rule=None,
            clause=current_clause,
            chapter=chapter,
            page=start_page,
            page_number=start_page,
            chunk_type="definition",
            title=c_title,
            section_title="Definitions",
            citation=citation
        )
        chunks.append(LegalChunk(
            chunk_id=c_id,
            text=f"{parent_ctx} | Clause ({current_clause}) '{current_term}':\n{c_text}",
            metadata=meta
        ))

    return chunks


def _split_rule6(lines_with_pages: List[Tuple[str, int]], doc_name: str, doc_title: str, chapter: str) -> List[LegalChunk]:
    """Splits Rule 6 into fine-grained chunks for mandatory retail declarations."""
    chunks = []
    parent_ctx = f"[{doc_title} | Chapter II: Provisions Applicable to Packages Intended for Retail Sale | Rule 6: Declarations to be made on every package]"

    clause_titles = {
        "a": "Name and address of manufacturer, packer or importer",
        "b": "Common or generic names of the commodity",
        "c": "Net quantity declaration in standard units of weight or measure or number",
        "d": "Month and year of manufacture or pre-packing or import",
        "e": "Retail sale price of the package (MRP)",
        "f": "Dimensions of the commodity contained in the package",
        "g": "Other matters and retail package declaration provisos"
    }
    subrule_titles = {
        "2": "Consumer Care / Complaint Contact Information",
        "3": "Prohibition of Individual Stickers on Package",
        "4": "Stickers for Non-Mandatory Declarations",
        "5": "Multi-Component Packages Sold as Single Commodity",
        "6": "Packaging Material Wrapper Transition"
    }

    current_sub = "1"
    current_clause = None
    current_lines = []
    start_page = 5

    def flush_chunk():
        if not current_lines:
            return
        c_text = "\n".join(current_lines)
        if current_sub == "1" and current_clause:
            c_title = clause_titles.get(current_clause, f"Rule 6(1)({current_clause})")
            c_id = f"rules2011_rule6_1_{current_clause}"
            citation = f"Rule 6(1)({current_clause}), {doc_title} (Page {start_page})"
            header_suffix = f"Sub-rule (1) Clause ({current_clause})"
        else:
            c_title = subrule_titles.get(current_sub, f"Rule 6({current_sub})")
            c_id = f"rules2011_rule6_{current_sub}"
            citation = f"Rule 6({current_sub}), {doc_title} (Page {start_page})"
            header_suffix = f"Sub-rule ({current_sub})"

        meta = ChunkMetadata(
            document=doc_name,
            document_name=doc_name,
            document_title=doc_title,
            rule="6",
            rule_number="6",
            sub_rule=current_sub,
            clause=current_clause,
            chapter=chapter,
            page=start_page,
            page_number=start_page,
            chunk_type="rule",
            title=c_title,
            section_title="Declarations to be made on every package",
            citation=citation
        )
        chunks.append(LegalChunk(
            chunk_id=c_id,
            text=f"{parent_ctx} | {header_suffix}:\n{c_text}",
            metadata=meta
        ))

    for line, page in lines_with_pages:
        sub_m = re.match(r'^\(([2-6])\)\s+(.+)', line)
        clause_m = re.match(r'^\(([a-g])\)\s+(.+)', line)

        if sub_m:
            flush_chunk()
            current_sub = sub_m.group(1)
            current_clause = None
            current_lines = [line]
            start_page = page
        elif clause_m and current_sub == "1":
            flush_chunk()
            current_clause = clause_m.group(1).lower()
            current_lines = [line]
            start_page = page
        else:
            current_lines.append(line)

    flush_chunk()
    return chunks


def _split_rule12(lines_with_pages: List[Tuple[str, int]], doc_name: str, doc_title: str, chapter: str) -> List[LegalChunk]:
    """Splits Rule 12 into sub-rule chunks, isolating 12(6) for misleading quantity qualifiers."""
    chunks = []
    parent_ctx = f"[{doc_title} | Chapter II | Rule 12: Manner in which declaration of quantity shall be made]"

    current_sub = None
    current_lines = []
    start_page = 12

    def flush_sub():
        if not current_sub or not current_lines:
            return
        c_text = "\n".join(current_lines)
        if current_sub == "6":
            c_title = "Prohibition of Misleading Quantity Qualifiers"
        else:
            c_title = f"Manner of Quantity Declaration - Rule 12({current_sub})"
        c_id = f"rules2011_rule12_{current_sub}"
        citation = f"Rule 12({current_sub}), {doc_title} (Page {start_page})"

        meta = ChunkMetadata(
            document=doc_name,
            document_name=doc_name,
            document_title=doc_title,
            rule="12",
            rule_number="12",
            sub_rule=current_sub,
            clause=None,
            chapter=chapter,
            page=start_page,
            page_number=start_page,
            chunk_type="rule",
            title=c_title,
            section_title="Manner in which declaration of quantity shall be made",
            citation=citation
        )
        chunks.append(LegalChunk(
            chunk_id=c_id,
            text=f"{parent_ctx} | Sub-rule ({current_sub}):\n{c_text}",
            metadata=meta
        ))

    for line, page in lines_with_pages:
        sub_m = re.match(r'^\*?\s*\((\d+)\)\s+(.+)', line)
        if sub_m:
            flush_sub()
            current_sub = sub_m.group(1)
            current_lines = [line]
            start_page = page
        else:
            current_lines.append(line)

    flush_sub()
    return chunks


def chunk_rules2009(pages: List[Dict[str, Any]]) -> List[LegalChunk]:
    """
    Produces section-aware chunks for the Legal Metrology Act, 2009.
    Preserves Sections 1 to 57 with parent chapter and penalty classifications.
    """
    doc_name = "rules2009.pdf"
    doc_title = DOC_TITLES[doc_name]
    chunks: List[LegalChunk] = []

    lines_with_pages: List[Tuple[str, int]] = []
    for p in pages:
        p_num = p["page_number"]
        # Skip pages 1 and 2 (Arrangement of Sections / Table of Contents)
        if p_num < 3:
            continue
        for line in p["cleaned_text"].split("\n"):
            line_str = line.strip()
            if line_str and not re.match(r'^\d+$', line_str):
                lines_with_pages.append((line_str, p_num))

    # Detect Section headers
    section_headers = []
    for idx, (line, p_num) in enumerate(lines_with_pages):
        sec_m = re.match(r'^(\d+)\.\s+([^\n]+)', line)
        if sec_m:
            num = int(sec_m.group(1))
            if num <= 57:
                title = sec_m.group(2).strip().rstrip(".-–—: ")
                section_headers.append({
                    "idx": idx,
                    "sec_num": str(num),
                    "title": title,
                    "page": p_num
                })

    section_headers.sort(key=lambda x: x["idx"])

    def get_act_chapter(sec_no: int) -> str:
        if sec_no <= 3:
            return "I: Preliminary"
        elif sec_no <= 12:
            return "II: Standard Weights and Measures"
        elif sec_no <= 23:
            return "III: Appointment and Powers of Legal Metrology Officers"
        elif sec_no <= 24:
            return "IV: Verification and Stamping"
        elif sec_no <= 49:
            return "V: Offences and Penalties"
        else:
            return "VI: Miscellaneous"

    for h_idx, h in enumerate(section_headers):
        start_line = h["idx"]
        end_line = section_headers[h_idx + 1]["idx"] if h_idx + 1 < len(section_headers) else len(lines_with_pages)
        sec_lines = lines_with_pages[start_line:end_line]
        sec_text = "\n".join(l[0] for l in sec_lines)
        start_page = h["page"]
        sec_int = int(h["sec_num"])
        chap = get_act_chapter(sec_int)

        c_type = "penalty" if 25 <= sec_int <= 49 else "section"
        c_id = f"rules2009_sec{h['sec_num']}"
        citation = f"Section {h['sec_num']}, {doc_title} (Page {start_page})"
        header_prefix = f"[{doc_title} | Chapter {chap} | Section {h['sec_num']}: {h['title']}]"
        full_chunk_text = f"{header_prefix}\n{sec_text}"

        meta = ChunkMetadata(
            document=doc_name,
            document_name=doc_name,
            document_title=doc_title,
            rule=h["sec_num"],
            rule_number=h["sec_num"],
            sub_rule=None,
            clause=None,
            chapter=chap.split(":")[0],
            page=start_page,
            page_number=start_page,
            chunk_type=c_type,
            title=f"Section {h['sec_num']}: {h['title']}",
            section_title=h["title"],
            citation=citation
        )
        chunks.append(LegalChunk(chunk_id=c_id, text=full_chunk_text, metadata=meta))

    return chunks


def ingest_documents(base_dir: Optional[str] = None) -> List[LegalChunk]:
    """
    Main entry point: Reads both legal PDFs, cleans text, and constructs
    all rule-aware chunks with metadata ready for ChromaDB indexing.
    """
    path_2009, path_2011 = resolve_pdf_paths(base_dir)
    
    pages_2011 = extract_pages_from_pdf(path_2011)
    chunks_2011 = chunk_rules2011(pages_2011)
    
    pages_2009 = extract_pages_from_pdf(path_2009)
    chunks_2009 = chunk_rules2009(pages_2009)
    
    all_chunks = chunks_2011 + chunks_2009
    
    # Validation assertions
    assert len(all_chunks) > 0, "No chunks were generated from the legal documents."
    for c in all_chunks:
        assert c.chunk_id, "Encountered chunk with missing ID"
        assert len(c.text.strip()) > 0, f"Encountered empty chunk text for ID: {c.chunk_id}"
        assert c.metadata.page > 0, f"Encountered invalid page number for chunk: {c.chunk_id}"
        assert c.metadata.document in DOC_TITLES, f"Unknown document in chunk: {c.chunk_id}"

    return all_chunks


def prepare_chroma_batches(chunks: List[LegalChunk]) -> Dict[str, List[Any]]:
    """
    Formats the list of LegalChunk objects into the exact structure
    expected by ChromaDB collection.add(ids=..., documents=..., metadatas=...).
    """
    ids = []
    documents = []
    metadatas = []
    seen_ids: Dict[str, int] = {}
    
    for c in chunks:
        cid = c.chunk_id
        if cid in seen_ids:
            seen_ids[cid] += 1
            unique_id = f"{cid}_{seen_ids[cid]}"
        else:
            seen_ids[cid] = 1
            unique_id = cid

        ids.append(unique_id)
        documents.append(c.text)
        metadatas.append(c.metadata.to_chroma_metadata())
        
    return {
        "ids": ids,
        "documents": documents,
        "metadatas": metadatas
    }


if __name__ == "__main__":
    print("================================================================================")
    print("LEGAL METROLOGY RAG INGESTION PIPELINE (5-DAY PROTOTYPE)")
    print("================================================================================")
    
    chunks = ingest_documents()
    print(f"\nSuccessfully ingested {len(chunks)} rule-aware legal chunks.")
    
    # Summary by document
    docs_count = {}
    for c in chunks:
        doc = c.metadata.document
        docs_count[doc] = docs_count.get(doc, 0) + 1
    for doc, count in docs_count.items():
        print(f"  - {doc} ({DOC_TITLES[doc]}): {count} chunks")
        
    # Verification of Core MVP Checks
    print("\n--- Key Compliance Rule Check Mappings ---")
    chunk_map = {c.chunk_id: c for c in chunks}
    key_verifications = [
        ("CHK-01: Product Name", "rules2011_rule6_1_b"),
        ("CHK-02: Net Quantity", "rules2011_rule6_1_c"),
        ("CHK-03: Retail Sale Price (MRP)", "rules2011_rule6_1_e"),
        ("CHK-04: Manufacturer / Packer", "rules2011_rule6_1_a"),
        ("CHK-05: Month & Year of Mfg", "rules2011_rule6_1_d"),
        ("CHK-06: Consumer Care Details", "rules2011_rule6_2"),
        ("CHK-07: Prohibited Qualifiers", "rules2011_rule12_6"),
        ("CHK-09: Importer / Origin", "rules2011_rule6_1_a"),
        ("Definition: Retail Sale Price (MRP)", "rules2011_rule2_m"),
        ("Parent Act: Pre-packaged Commodities", "rules2009_sec18"),
        ("Parent Act: Penalties", "rules2009_sec36"),
    ]
    
    for label, cid in key_verifications:
        if cid in chunk_map:
            c = chunk_map[cid]
            print(f"  [OK] {label:<38} -> ID: {cid:<24} | Page {c.metadata.page:>2} | {c.metadata.citation}")
        else:
            print(f"  [MISSING] {label} -> {cid}")
            
    # Sample Chroma Batch
    chroma_batch = prepare_chroma_batches(chunks)
    print(f"\nChromaDB Batch Prepared: {len(chroma_batch['ids'])} vectors ready for embedding.")
    print("================================================================================")

"""
Demonstration script for RAG + Compliance Engine integration (Person 6).

Demonstrates the compliance engine with LegalRetriever attaching verbatim
citations from rules2011.pdf to each active check result.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure Windows console supports UTF-8 characters safely
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.compliance.schemas import StructuredFacts, ComplianceResult
from backend.compliance.engine import run_compliance_checks
from backend.rag.retriever import LegalRetriever


def run_rag_demo():
    fixture_path = PROJECT_ROOT / "tests" / "golden_data" / "compliant_biscuit.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        raw_facts = json.load(f)

    # 1. Parse JSON fixture using canonical StructuredFacts schema
    facts = StructuredFacts(**raw_facts)

    # 2. Initialize existing LegalRetriever
    retriever = LegalRetriever()

    # 3. Run compliance checks with RAG retriever attached
    result: ComplianceResult = run_compliance_checks(facts, retriever=retriever)

    print("========================================")
    print("RAG + COMPLIANCE DEMONSTRATION")
    print("========================================")
    print()
    print(f"Overall Status:        {result.overall_status}")
    print(f"Automated Check Score: {result.automated_check_score:.1f}%")
    print()

    rag_retrieval_ok = True
    legal_citations_ok = True
    compliance_engine_ok = (result.overall_status == "PASS" and result.automated_check_score == 100.0)

    for c in result.checks:
        conf_str = f"{c.confidence:.2f}" if c.confidence is not None else "N/A"
        citation = c.legal_source.citation if c.legal_source else "None"
        page = str(c.legal_source.page) if c.legal_source else "None"
        legal_text = c.legal_source.text if c.legal_source else "None"

        if not c.legal_source or not c.legal_source.citation or not c.legal_source.page:
            legal_citations_ok = False
            rag_retrieval_ok = False

        print(f"- Check ID:        {c.check_id}")
        print(f"  Rule Name:       {c.rule_name}")
        print(f"  Status:          {c.status}")
        print(f"  Detected Value:  {c.detected_value}")
        print(f"  Confidence:      {conf_str}")
        print(f"  Legal Citation:  {citation}")
        print(f"  Legal Page:      {page}")
        print(f"  Legal Text:      {legal_text[:140]}...")
        print(f"  Reason:          {c.reason}")
        print()

    # Explicit spotlight on CHK-03 and CHK-06
    print("========================================")
    print("SPOTLIGHT: RETRIEVED LEGAL SOURCES")
    print("========================================")

    check_map = {c.check_id: c for c in result.checks}

    # CHK-03 (MRP)
    c03 = check_map.get("CHK-03")
    print("\n[CHK-03: Maximum Retail Price (MRP)]")
    if c03 and c03.legal_source:
        print(f"Citation:    {c03.legal_source.citation}")
        print(f"Source Page: Page {c03.legal_source.page}")
        print(f"Document:    {c03.legal_source.document}")
        print("Verbatim Legal Text:")
        print("-" * 60)
        print(c03.legal_source.text.strip())
        print("-" * 60)
    else:
        print("Legal source not retrieved.")

    # CHK-06 (Consumer Care)
    c06 = check_map.get("CHK-06")
    print("\n[CHK-06: Consumer Care / Grievance Redressal]")
    if c06 and c06.legal_source:
        print(f"Citation:    {c06.legal_source.citation}")
        print(f"Source Page: Page {c06.legal_source.page}")
        print(f"Document:    {c06.legal_source.document}")
        print("Verbatim Legal Text:")
        print("-" * 60)
        print(c06.legal_source.text.strip())
        print("-" * 60)
    else:
        print("Legal source not retrieved.")

    overall_ok = (rag_retrieval_ok and compliance_engine_ok and legal_citations_ok and result.overall_status == "PASS")

    print("\n========================================")
    print("VERIFICATION EVALUATION")
    print("========================================")
    print(f"RAG retrieval:     {'PASS' if rag_retrieval_ok else 'FAIL'}")
    print(f"Compliance engine: {'PASS' if compliance_engine_ok else 'FAIL'}")
    print(f"Legal citations:   {'PASS' if legal_citations_ok else 'FAIL'}")
    print(f"Overall result:    {'PASS' if overall_ok else 'FAIL'}")
    print("========================================")


if __name__ == "__main__":
    run_rag_demo()

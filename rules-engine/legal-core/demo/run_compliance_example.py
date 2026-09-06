"""
Manual demonstration script for Legal Metrology Compliance Engine (Person 6).

Demonstrates pure deterministic compliance validation on golden JSON fixtures
completely independent of OCR and RAG retrieval.
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

CASES = [
    {
        "filename": "compliant_biscuit.json",
        "expected": "PASS",
        "description": "All mandatory declarations present with high confidence and valid SI/MRP format."
    },
    {
        "filename": "missing_mrp.json",
        "expected": "FAIL",
        "description": "MRP declaration is completely omitted from high-confidence packaging."
    },
    {
        "filename": "mrp_no_tax.json",
        "expected": "FAIL",
        "description": "MRP is declared without the mandatory 'inclusive of all taxes' clause."
    },
    {
        "filename": "blurry_low_conf.json",
        "expected": "REVIEW",
        "description": "Low-quality/blurry packaging triggering manual review threshold (<0.70)."
    }
]


def run_demo():
    print("\n" + "=" * 80)
    print("      PACKAGED COMMODITIES COMPLIANCE ENGINE — OFFLINE DETERMINISTIC DEMO      ")
    print("=" * 80)
    print("Mode: Standalone Pure-Python Evaluation (Zero LLM, Zero Network Calls, RAG Bypassed)")
    print("Rules: Legal Metrology (Packaged Commodities) Rules, 2011 (CHK-01 to CHK-06)\n")

    summary_rows = []

    for case_info in CASES:
        fname = case_info["filename"]
        expected_status = case_info["expected"]
        file_path = PROJECT_ROOT / "tests" / "golden_data" / fname

        with open(file_path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)

        # 1. Parse using canonical StructuredFacts schema
        facts = StructuredFacts(**raw_json)

        # 2. Run deterministic compliance checks
        result: ComplianceResult = run_compliance_checks(facts, retriever=None)

        print("=" * 60)
        print(f"CASE: {fname}")
        print("=" * 60)
        print(f"Description:           {case_info['description']}")
        print(f"Overall Status:        {result.overall_status}")
        print(f"Automated Check Score: {result.automated_check_score:.1f}%")
        print(f"Summary:               Passed: {result.summary.passed}/{result.summary.total_checks} | Failed: {result.summary.failed} | Review: {result.summary.review}")
        print("\nIndividual Checks:")
        print("-" * 60)

        violations = []
        reviews = []

        for c in result.checks:
            conf_str = f"{c.confidence:.2f}" if c.confidence is not None else "N/A"
            citation = c.legal_source.citation if c.legal_source else "N/A (RAG bypassed for offline demo)"
            page = str(c.legal_source.page) if c.legal_source else "N/A"

            print(f"- Check ID:        {c.check_id}")
            print(f"  Rule Name:       {c.rule_name}")
            print(f"  Status:          {c.status} ({c.severity})")
            print(f"  Detected Value:  {c.detected_value}")
            print(f"  Confidence:      {conf_str}")
            print(f"  Reason:          {c.reason}")
            print(f"  Legal Citation:  {citation}")
            print(f"  Legal Page:      {page}")
            print()

            if c.status == "FAIL":
                violations.append(f"[{c.check_id}] {c.rule_name}: {c.reason}")
            elif c.status == "REVIEW":
                reviews.append(f"[{c.check_id}] {c.rule_name}: {c.reason}")

        print("Violations:")
        if violations:
            for v in violations:
                print(f"  ❌ {v}")
        else:
            print("  (None — No statutory violations detected)")

        if reviews:
            print("\nFlagged for Manual Review:")
            for r in reviews:
                print(f"  ⚠️  {r}")

        print("\nDisclaimers:")
        for d in result.disclaimers:
            print(f"  ℹ️  {d}")

        print("\n")

        # Track for summary table
        matched = (result.overall_status == expected_status)
        result_icon = "✓" if matched else "✗"
        summary_rows.append({
            "case": fname,
            "expected": expected_status,
            "actual": result.overall_status,
            "result": result_icon,
            "score": f"{result.automated_check_score:.1f}%"
        })

    # 3. Compact Final Summary Table
    print("=" * 70)
    print("FINAL DEMONSTRATION SUMMARY")
    print("=" * 70)
    print(f"{'Case':<28} {'Expected':<12} {'Actual':<12} {'Score':<10} {'Result'}")
    print("-" * 70)
    all_passed = True
    for row in summary_rows:
        print(f"{row['case']:<28} {row['expected']:<12} {row['actual']:<12} {row['score']:<10} {row['result']}")
        if row["result"] != "✓":
            all_passed = False
    print("-" * 70)

    if all_passed:
        print("ALL 4 DEMONSTRATION CASES MATCHED THEIR EXPECTED OUTCOMES EXACTLY.")
    else:
        print("ONE OR MORE DEMONSTRATION CASES FAILED TO MATCH EXPECTED OUTCOMES.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_demo()

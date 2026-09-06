"""
Integration Orchestrator for Legal Metrology Compliance System.
Connects Person 5 AI Engine (facts extraction) with Person 6 Legal Compliance Engine (legal rules & citations).
"""

import os
import sys
from typing import Optional, Dict, Any

# Ensure ai-engine and rules-engine/legal-core are on sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.abspath(os.path.join(_current_dir, ".."))

_ai_dir = os.path.join(_repo_root, "ai-engine")
if _ai_dir not in sys.path:
    sys.path.insert(0, _ai_dir)

_legal_dir = os.path.join(_repo_root, "rules-engine", "legal-core")
if _legal_dir not in sys.path:
    sys.path.insert(0, _legal_dir)

from analyzer import analyze_image, analyze_multi_image
from backend.compliance.adapter import ai_result_to_structured_facts
from backend.compliance.engine import run_compliance_checks
from backend.rag.retriever import LegalRetriever


def run_full_inspection(
    front_path: str,
    back_path: str,
    side_path: Optional[str] = None,
    demo_mode: bool = False,
    use_rag: bool = False,
) -> Dict[str, Any]:
    """
    Runs full multi-image inspection pipeline:
    1. Person 5 AI Engine extracts raw text & field detections from front, back, and optional side images.
    2. Person 6 Adapter maps and normalizes detections into StructuredFacts.
    3. Person 6 Legal Engine verifies compliance against Legal Metrology Rules (CHK-01 to CHK-06),
       optionally retrieving legal citations via RAG.
    """
    ai_result = analyze_multi_image(
        front_image_path=front_path,
        back_image_path=back_path,
        side_image_path=side_path,
        demo_mode=demo_mode,
    )

    if not ai_result.get("success", False):
        return {
            "ai_result": ai_result,
            "structured_facts": None,
            "compliance_result": None,
        }

    facts = ai_result_to_structured_facts(ai_result)
    retriever = LegalRetriever() if use_rag else None
    compliance_result = run_compliance_checks(facts, retriever=retriever)

    return {
        "ai_result": ai_result,
        "structured_facts": facts.model_dump(),
        "compliance_result": compliance_result.model_dump(),
    }


def run_single_image_inspection(
    image_path: str,
    demo_mode: bool = False,
    use_rag: bool = False,
) -> Dict[str, Any]:
    """
    Runs single-image inspection pipeline through AI Engine, Adapter, and Legal Compliance Engine.
    """
    ai_result = analyze_image(
        image_path=image_path,
        demo_mode=demo_mode,
    )

    if not ai_result.get("success", False):
        return {
            "ai_result": ai_result,
            "structured_facts": None,
            "compliance_result": None,
        }

    facts = ai_result_to_structured_facts(ai_result)
    retriever = LegalRetriever() if use_rag else None
    compliance_result = run_compliance_checks(facts, retriever=retriever)

    return {
        "ai_result": ai_result,
        "structured_facts": facts.model_dump(),
        "compliance_result": compliance_result.model_dump(),
    }


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Run end-to-end Legal Metrology inspection on package image(s)."
    )
    parser.add_argument("image_path", nargs="?", default=None, help="Single image path")
    parser.add_argument("--front", type=str, default=None, help="Front label image path")
    parser.add_argument("--back", type=str, default=None, help="Back label image path")
    parser.add_argument("--side", type=str, default=None, help="Side label image path (optional)")
    parser.add_argument("--rag", action="store_true", default=False, help="Enable Legal RAG citations from ChromaDB")
    parser.add_argument("--demo", action="store_true", default=False, help="Enable demo mode fallback")
    parser.add_argument("--json", action="store_true", default=False, help="Output raw JSON instead of formatted report")

    args = parser.parse_args()

    if args.front and args.back:
        print(f"[*] Running multi-image inspection (front: {args.front}, back: {args.back})...")
        res = run_full_inspection(args.front, args.back, args.side, demo_mode=args.demo, use_rag=args.rag)
    elif args.image_path:
        print(f"[*] Running single-image inspection: {args.image_path}...")
        res = run_single_image_inspection(args.image_path, demo_mode=args.demo, use_rag=args.rag)
    else:
        parser.print_help()
        sys.exit(1)

    if args.json:
        print(json.dumps(res, indent=2))
        return

    ai_res = res["ai_result"]
    facts = res["structured_facts"]
    comp = res["compliance_result"]

    if not ai_res.get("success"):
        print("\n❌ Inspection failed during AI analysis stage:")
        for err in ai_res.get("errors", []):
            print(f"   - {err.get('message', 'Unknown error')}")
        return

    print("\n" + "=" * 65)
    print(" 📦 LEGAL METROLOGY COMPLIANCE REPORT")
    print("=" * 65)
    print(f" Overall Status   : {comp['overall_status']}")
    print(f" Compliance Score : {comp.get('automated_check_score', 0)}%")
    print(f" Processing Time  : {ai_res.get('processing_time_ms', 0)} ms")
    print("-" * 65)

    print("\n🔍 1. EXTRACTED FACTS (PERSON 5 AI ENGINE):")
    print(f"{'Field':<28} | {'Status':<14} | {'Conf':<6} | {'Value'}")
    print("-" * 65)
    for det in ai_res.get("detections", []):
        field_name = det.get("label") or det.get("field")
        status = det.get("status", "not_found")
        conf = f"{det.get('confidence', 0.0):.2f}"
        val = str(det.get("value") or "-")
        if len(val) > 25:
            val = val[:22] + "..."
        print(f"{field_name:<28} | {status:<14} | {conf:<6} | {val}")

    print("\n⚖️  2. LEGAL CHECKS EVALUATION (PERSON 6 RULES ENGINE):")
    print(f"{'Check ID':<8} | {'Status':<8} | {'Severity':<10} | {'Reason'}")
    print("-" * 65)
    for chk in comp.get("checks", []):
        cid = chk.get("check_id")
        cstatus = chk.get("status")
        csev = chk.get("severity", "-")
        creason = chk.get("reason", "")
        if len(creason) > 35:
            creason = creason[:32] + "..."
        print(f"{cid:<8} | {cstatus:<8} | {csev:<10} | {creason}")

    if args.rag:
        print("\n📚 3. LEGAL CITATIONS (RAG):")
        for chk in comp.get("checks", []):
            source = chk.get("legal_source")
            if source:
                rule_str = f" - Rule {source.get('rule')}" if source.get('rule') else ""
                print(f" [{chk.get('check_id')}]: {source.get('citation', '')}{rule_str}")


    print("\n" + "=" * 65 + "\n")


if __name__ == "__main__":
    main()


"""
Compliance Engine Orchestrator for Legal Metrology Packaged Commodities.

Coordinates:
1. Retrieval of authoritative legal context via LegalRetriever (top-3 results per check).
2. Execution of pure-python deterministic validators (CHK-01 to CHK-06).
3. Aggregation of statuses, scoring, and generation of ComplianceResult.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict

from backend.compliance.schemas import (
    StructuredFacts,
    ComplianceResult,
    ComplianceSummary,
    CheckResult,
    LegalSource
)
from backend.compliance.checks import CORE_CHECKS
from backend.rag.retriever import LegalRetriever, RetrievedContext

STANDARD_DISCLAIMERS = [
    "AI-assisted preliminary assessment under Legal Metrology Rules, 2011.",
    "Absence of text in single-angle OCR does not guarantee absence on non-visible physical package panels.",
    "Official enforcement requires verification by an authorized Legal Metrology Officer."
]


def run_compliance_checks(
    facts: StructuredFacts,
    retriever: Optional[LegalRetriever] = None,
    k_legal: int = 3
) -> ComplianceResult:
    """
    Executes the active Core MVP compliance checks on structured packaging facts.

    Args:
        facts: Canonical StructuredFacts extracted from OCR/image.
        retriever: Optional LegalRetriever instance for attaching RAG citations.
        k_legal: Number of legal chunks to retrieve (default: 3).

    Returns:
        ComplianceResult containing summary, check results with evidence & legal sources.
        Note: automated_check_score is a prototype summary metric and NOT an official legal metric.
    """
    check_results: List[CheckResult] = []

    for check_id, check_fn in CORE_CHECKS.items():
        legal_source: Optional[LegalSource] = None

        if retriever is not None:
            try:
                retrieved_list: List[RetrievedContext] = retriever.retrieve_for_check(check_id, k=k_legal)
                if retrieved_list:
                    best_match = retrieved_list[0]
                    legal_source = LegalSource(
                        citation=best_match.citation,
                        page=best_match.page,
                        text=best_match.text,
                        document=best_match.document,
                        rule=best_match.rule,
                        sub_rule=best_match.sub_rule,
                        clause=best_match.clause
                    )
            except Exception as e:
                # Retriever error should not crash deterministic checks
                legal_source = None

        result = check_fn(facts, legal_source=legal_source)
        check_results.append(result)

    # Statistical Summary
    total_checks = len(check_results)
    passed = sum(1 for c in check_results if c.status == "PASS")
    failed = sum(1 for c in check_results if c.status == "FAIL")
    review = sum(1 for c in check_results if c.status == "REVIEW")
    not_applicable = sum(1 for c in check_results if c.status == "N/A")

    summary = ComplianceSummary(
        total_checks=total_checks,
        passed=passed,
        failed=failed,
        review=review,
        not_applicable=not_applicable
    )

    # Overall Status Decision Tree
    if failed > 0:
        overall_status = "FAIL"
    elif review > 0:
        overall_status = "REVIEW"
    else:
        overall_status = "PASS"

    # Automated check score calculation (prototype summary metric, and NOT an official legal metric)
    applicable_checks = total_checks - not_applicable
    score = round((passed / applicable_checks) * 100.0, 1) if applicable_checks > 0 else 0.0

    return ComplianceResult(
        inspection_id=facts.inspection_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        overall_status=overall_status,
        automated_check_score=score,
        summary=summary,
        checks=check_results,
        disclaimers=list(STANDARD_DISCLAIMERS)
    )

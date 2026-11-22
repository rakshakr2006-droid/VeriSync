"""
Module: core/pipeline.py
Owner: P4 (forgery/verdict/app/repo)

Purpose:
End-to-end verification pipeline coordinating claim extraction, retrieval,
evidence verification, forgery checks, and final verdict determination.
"""
from typing import Dict, Any, Optional, Set

from core.claim_extractor import extract_claim
from core.retriever import search
from core.verifier import verify
from core.forgery_rules import check_forgery
from core.verdict import decide


def known_numbers() -> Optional[Set[str]]:
    """
    Return set of known circular numbers indexed in the system.
    Returns None if known circular repository is not yet available.
    """
    # TODO [P1/P2]: Return all indexed circular numbers from database / index metadata
    return None


def verify_notice(message: str) -> Dict[str, Any]:
    """
    Run end-to-end verification on a forwarded notice.

    Args:
        message: Raw text of forwarded circular or notice.

    Returns:
        dict: {
            "verdict": "Verified" | "Contradicted" | "Unverified",
            "claim": dict,
            "evidence": dict,
            "flags": list,
            "hits": list
        }
    """
    # 1. Extract claim
    claim = extract_claim(message)

    # 2. Build query from claim fields (fall back to raw message)
    query_parts = [
        str(v)
        for k, v in claim.items()
        if v and k in ("event", "exam", "circular_no", "new_date")
    ]
    query = " ".join(query_parts).strip() if query_parts else message.strip()

    # 3. Search evidence
    hits = search(query)

    # 4. Verify claim against evidence
    evidence = verify(claim, hits)

    # 5. Check forgery rules
    flags = check_forgery(claim, known_numbers=known_numbers())

    # 6. Decide final verdict
    verdict = decide(evidence.get("result", "not_found"), flags)

    return {
        "verdict": verdict,
        "claim": claim,
        "evidence": evidence,
        "flags": flags,
        "hits": hits,
    }

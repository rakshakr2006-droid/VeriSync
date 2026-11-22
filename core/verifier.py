"""
Module: core/verifier.py
Owner: P3 (LLM/claims/verifier)

Purpose:
Compare extracted claims against retrieved circular evidence clauses to verify consistency.
"""
from typing import Dict, Any, List


def verify(claim: Dict[str, Any], hits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    STUB, owner replaces this.

    Verify an extracted claim against retrieved circular hits.

    Args:
        claim: Dict containing extracted claims.
        hits: List of retrieved search hit dictionaries.

    Returns:
        dict: {
            "result": "supports" | "contradicts" | "not_found",
            "circular_no": str or None,
            "file": str or None,
            "page": int or None,
            "clause": str or None
        }
    """
    if hits:
        top_hit = hits[0]
        return {
            "result": "contradicts",
            "circular_no": top_hit.get("circular_no"),
            "file": top_hit.get("file"),
            "page": top_hit.get("page"),
            "clause": top_hit.get("text"),
        }

    return {
        "result": "not_found",
        "circular_no": None,
        "file": None,
        "page": None,
        "clause": None,
    }

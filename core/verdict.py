"""
Module: core/verdict.py
Owner: P4 (forgery/verdict/app/repo)

Purpose:
Determine final status from verification result and detected forgery flags.
"""
from typing import List, Dict


def decide(result: str, flags: List[Dict[str, str]]) -> str:
    """
    Compute final verdict string from verification result and flags.

    Decision rules:
    - result == "contradicts" -> "Contradicted"
    - result == "supports" and no hard flag -> "Verified"
    - everything else (including "not_found") -> "Unverified"
    NOT FOUND MUST NEVER BE CALLED FAKE.

    Args:
        result: Verification result ("supports", "contradicts", "not_found").
        flags: List of forgery flag dicts with 'severity' key ('hard' | 'soft').

    Returns:
        "Verified" | "Contradicted" | "Unverified"
    """
    if result == "contradicts":
        return "Contradicted"

    has_hard_flag = any(f.get("severity") == "hard" for f in flags)

    if result == "supports" and not has_hard_flag:
        return "Verified"

    return "Unverified"

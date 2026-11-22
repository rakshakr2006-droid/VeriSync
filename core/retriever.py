"""
Module: core/retriever.py
Owner: P2 (index/search/evaluation)

Purpose:
Retrieve relevant circular clauses given a query string.
"""
from typing import List, Dict, Any


def search(text: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    STUB, owner replaces this.

    Search for matching circular chunks given query text.

    Args:
        text: Query string.
        k: Number of hits to return.

    Returns:
        List of dicts: {"text", "circular_no", "date", "file", "page", "score"}
    """
    # Fake stub hit
    return [
        {
            "text": "Dummy clause: exams will be held on 5 December 2026.",
            "circular_no": "VTU/DUMMY/1",
            "date": "2026-11-20",
            "file": "dummy.pdf",
            "page": 1,
            "score": 0.99,
        }
    ]

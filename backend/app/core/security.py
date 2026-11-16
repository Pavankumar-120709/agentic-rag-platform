"""
Security middleware, prompt injection defense, and input sanitation.
"""
import re
import hashlib
from typing import Tuple


# Common prompt injection signatures to detect and neutralize
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
    re.compile(r"you\s+are\s+no\s+longer\s+bound", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"\[INST\].*\[/INST\]", re.IGNORECASE),
]


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Scans incoming user query or untrusted document content for prompt injection triggers.
    Returns (is_detected, matched_pattern).
    """
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)
    return False, ""


def compute_sha256(content: bytes) -> str:
    """Computes SHA-256 hash of binary content for document deduplication."""
    hasher = hashlib.sha256()
    hasher.update(content)
    return hasher.hexdigest()


def sanitize_text(text: str) -> str:
    """Removes null bytes and control characters while preserving standard unicode and whitespace."""
    if not text:
        return ""
    # Strip null bytes and non-printable control characters except newline and tab
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

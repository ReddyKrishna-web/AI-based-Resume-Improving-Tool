"""
Text cleaning utilities used by the parser and structurer.

Kept separate so the cleaning pipeline is independently testable
and auditable — no magic regexes hidden inside service logic.
"""

from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces,
    preserving paragraph breaks."""
    # Replace all horizontal whitespace (spaces, tabs) with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize paragraph breaks to \n\n
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_line(line: str) -> str:
    """Remove common PDF artifacts from a single line."""
    # Remove soft hyphens (common in justified PDF text)
    line = line.replace("\u00ad", "")
    # Remove ligature artifacts
    line = line.replace("\ufb00", "ff").replace("\ufb01", "fi")
    line = line.replace("\ufb02", "fl").replace("\ufb03", "ffi")
    line = line.replace("\ufb04", "ffl")
    # Remove control chars except newline and tab
    line = "".join(c if c == "\n" or c == "\t" or ord(c) >= 32 else "" for c in line)
    return line.strip()


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text."""
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text)


def extract_phones(text: str) -> list[str]:
    """Extract phone numbers (various formats)."""
    patterns = [
        r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    ]
    phones: list[str] = []
    for pat in patterns:
        phones.extend(re.findall(pat, text))
    return phones


def extract_urls(text: str) -> list[str]:
    """Extract URLs (particularly LinkedIn/GitHub)."""
    pattern = r"https?://(?:www\.)?[a-zA-Z0-9./%?#=-]+[a-zA-Z0-9/]"
    return re.findall(pattern, text)


def detect_language(text: str) -> str:
    """Detect whether text is primarily English based on character range.
    Returns 'en' or 'other'.

    This is deliberately simplistic — just enough to warn users that
    ATS scoring is English-optimized. A production system would use
    a language-detection library like langdetect or fastText.
    """
    if not text.strip():
        return "en"
    # Count ASCII vs non-ASCII letters
    ascii_count = sum(1 for c in text if "a" <= c.lower() <= "z" or c in " .,!?;:'\"-")
    total_letters = sum(1 for c in text if c.isalpha())
    if total_letters == 0:
        return "en"
    ratio = ascii_count / total_letters
    return "en" if ratio > 0.8 else "other"


def split_into_bullets(text: str) -> list[str]:
    """Split text into individual bullet points.

    Handles common bullet characters and numbered lists.
    """
    # Normalize bullet characters to a standard marker
    text = re.sub(r"[•●◦‣⁃▪▸▹►›]", "•", text)
    # Split on bullet markers or numbers at start of line
    lines = re.split(r"\n\s*(?:•|[\d]+[.)])\s*|\n\s*(?=\d+[.)]\s)", text)
    # Also split on regular newlines as fallback
    if len(lines) <= 1:
        lines = text.strip().split("\n")
    return [l.strip() for l in lines if l.strip()]


def has_metric(text: str) -> bool:
    """Check if a bullet point contains quantified metrics (%, $, numbers)."""
    return bool(re.search(r"\d+[%×x]?|\$\d+|\d+%|\d+x", text))


def has_strong_verb(text: str, strong_verbs: set[str]) -> bool:
    """Check if a bullet starts with a strong action verb."""
    first_word = text.strip().split()[0].lower().rstrip(".,;:") if text.strip() else ""
    return first_word in strong_verbs

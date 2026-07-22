"""
Keyword/ATS matcher — compares resume content against a job description
or generic ATS ruleset.

Architectural decision: Keyword extraction from the JD uses simple NLP
(part-of-speech filtering + TF-IDF noun phrases from the job description).
No LLM is used for matching — the matching logic is deterministic and
explainable. When no JD is provided, we fall back to the hardcoded
keyword bank in ats_rules.py.

This separation means the scoring is always reproducible: two runs with
the same inputs produce identical results.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from app.models.schemas import (
    FormattingIssue,
    MatchResult,
    StructuredResume,
)
from app.utils.ats_rules import GENERAL_SKILLS

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────
MIN_KEYWORD_LENGTH = 3
MAX_KEYWORD_NGRAM = 3


def analyze(
    resume: StructuredResume,
    jd_text: Optional[str] = None,
    formatting_warnings: Optional[list[str]] = None,
) -> MatchResult:
    """Main entry point: analyze resume against JD or generic rules.

    Args:
        resume: Structured resume data.
        jd_text: Raw job description text, or None for generic matching.
        formatting_warnings: Warnings from the parser step.

    Returns:
        MatchResult with keyword gaps, match percentages, and formatting issues.
    """
    # Build the set of all unique words/phrases from the resume
    resume_text = _resume_to_text(resume)
    resume_words = set(_tokenize(resume_text))

    if jd_text and jd_text.strip():
        return _match_against_jd(resume, resume_words, jd_text)
    else:
        return _match_against_generic(resume, resume_words, formatting_warnings)


# ── JD-based matching ─────────────────────────────────────


def _match_against_jd(
    resume: StructuredResume,
    resume_words: set[str],
    jd_text: str,
) -> MatchResult:
    """Match resume against a specific job description."""
    jd_keywords = _extract_jd_keywords(jd_text)
    jd_keywords_lower = [kw.lower() for kw in jd_keywords]

    matched = []
    missing = []
    for kw in jd_keywords_lower:
        # Check if the keyword appears in any resume text
        if kw in resume_words or _fuzzy_match(kw, resume_words):
            matched.append(kw)
        else:
            missing.append(kw)

    match_pct = (len(matched) / len(jd_keywords)) * 100 if jd_keywords else 100.0

    return MatchResult(
        jd_provided=True,
        matched_keywords=matched,
        missing_keywords=missing,
        keyword_match_pct=round(match_pct, 1),
    )


def _extract_jd_keywords(jd_text: str) -> list[str]:
    """Extract meaningful keywords from a job description.

    Uses a simple approach: collect title-cased words/phrases,
    skill-like terms, and single words that look like programming
    languages or tools.
    """
    jd_lower = jd_text.lower()
    keywords: list[str] = []

    # 1. Extract n-grams (1-3 words) that start with capital letters
    #    These are usually proper nouns, technologies, company names
    sentences = re.split(r"[.\n;]", jd_text)
    for sent in sentences:
        # Find capitalized phrases (likely tech names, tools, etc.)
        capitalized = re.findall(r"\b([A-Z][a-zA-Z+#.0-9]+(?:\s[A-Z][a-zA-Z+#.0-9]+){0,2})\b", sent)
        keywords.extend(c.lower() for c in capitalized if len(c) >= MIN_KEYWORD_LENGTH)

    # 2. Add ALL single words from the JD that appear in our GENERAL_SKILLS list
    #    (this catches skills mentioned in lowercase in the JD)
    jd_words = _tokenize(jd_lower)
    for skill in GENERAL_SKILLS:
        if skill in jd_lower:
            keywords.append(skill)

    # 3. Look for common keyword indicators
    for pattern in [
        r"(?:proficient in|experience with|knowledge of|familiar with|expertise in)\s+([\w\s+#.]+?)(?:,|;|\.|\n)",
        r"(?:using|including such as)\s+([\w\s+#.]+?)(?:,|;|\.|\n)",
    ]:
        matches = re.findall(pattern, jd_text, re.IGNORECASE)
        for match in matches:
            # Split comma-separated items
            for item in re.split(r"[,;/]", match):
                item = item.strip().lower()
                if len(item) >= MIN_KEYWORD_LENGTH and item not in keywords:
                    keywords.append(item)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_keywords: list[str] = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    return unique_keywords[:50]  # Limit to top 50 keywords


# ── Generic (no-JD) matching ──────────────────────────────


def _match_against_generic(
    resume: StructuredResume,
    resume_words: set[str],
    formatting_warnings: Optional[list[str]] = None,
) -> MatchResult:
    """Match resume against generic ATS keyword bank."""
    matched = []
    missing = []

    for skill in GENERAL_SKILLS:
        skill_lower = skill.lower()
        if skill_lower in resume_words or _fuzzy_match(skill_lower, resume_words):
            matched.append(skill)
        else:
            missing.append(skill)

    match_pct = (len(matched) / len(GENERAL_SKILLS)) * 100

    formatting_issues = _check_formatting_issues(resume_text="\n".join(resume_words))

    return MatchResult(
        jd_provided=False,
        matched_keywords=matched,
        missing_keywords=missing,
        keyword_match_pct=round(match_pct, 1),
        formatting_issues=formatting_issues,
    )


# ── Formatting checks ─────────────────────────────────────


def _check_formatting_issues(resume_text: str) -> list[FormattingIssue]:
    """Check for common ATS-unfriendly formatting patterns."""
    issues: list[FormattingIssue] = []

    # Check for very long lines (possible table remnants)
    for line in resume_text.split("\n"):
        if len(line) > 200:
            issues.append(FormattingIssue(
                issue_type="long_line",
                severity="warning",
                message="Very long line detected — possible table or multi-column content. "
                        "Some ATS parsers may misread this.",
            ))
            break

    # Check for special characters that break parsers
    special_ratio = sum(1 for c in resume_text if ord(c) > 127) / max(len(resume_text), 1)
    if special_ratio > 0.05:
        issues.append(FormattingIssue(
            issue_type="special_characters",
            severity="warning",
            message="Unusual characters detected (e.g., non-ASCII symbols). "
                    "These can cause encoding issues in ATS databases.",
        ))

    return issues


# ── Helpers ───────────────────────────────────────────────


def _resume_to_text(resume: StructuredResume) -> str:
    """Flatten structured resume into a searchable text blob."""
    parts: list[str] = []

    if resume.summary:
        parts.append(resume.summary)
    for edu in resume.education:
        parts.extend([edu.institution, edu.degree, edu.field])
    for exp in resume.experience:
        parts.append(exp.company)
        parts.append(exp.title)
        for bullet in exp.bullets:
            parts.append(bullet.text)
    parts.extend(resume.skills)
    for proj in resume.projects:
        parts.append(proj.name)
        parts.append(proj.description)
        parts.extend(proj.technologies)
    parts.extend(resume.certifications)

    return " ".join(p for p in parts if p)


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens (words and simple n-grams)."""
    # Remove punctuation (keep hyphens and dots for tech names)
    text = re.sub(r"[^\w\s\-+#.]", " ", text.lower())
    words = text.split()
    result: list[str] = []

    # Single words
    result.extend(words)

    # Bigrams and trigrams (for compound terms like "machine learning")
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        result.append(bigram)

    for i in range(len(words) - 2):
        trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
        result.append(trigram)

    return result


def _fuzzy_match(keyword: str, resume_words: set[str]) -> bool:
    """Check if a keyword appears as a substring of any resume word/phrase.

    This catches cases where the resume says "postgresql" and the JD says
    "postgres", or "react.js" vs "react". It's deliberately forgiving —
    better to have a few false positives than miss a legitimate match.
    """
    keyword_lower = keyword.lower()
    for rw in resume_words:
        if keyword_lower in rw or rw in keyword_lower:
            return True
    return False

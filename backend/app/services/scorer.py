"""
Scoring engine — produces a 0-100 ATS-compatibility score with a
fully transparent breakdown.

Architectural decision: This is PURELY rule-based. No LLM is involved
in scoring. This is a critical interview talking point:
- **Deterministic**: Same resume + same JD always gives the same score.
- **Auditable**: Each category has a clear explanation of why that score was given.
- **Extensible**: Weights and thresholds can be adjusted based on user feedback.

Score categories and their weights:
  - Keyword Coverage (40%) — How many required keywords were found.
  - Section Completeness (20%) — Are all expected resume sections present?
  - Formatting Quality (15%) — Penalties for ATS-unfriendly formatting.
  - Action Verb Usage (15%) — Ratio of strong vs. weak verbs in bullets.
  - Quantification (10%) — Presence of metrics and numbers in experience bullets.
"""

from __future__ import annotations

import logging

from app.models.schemas import (
    CategoryScore,
    MatchResult,
    ScoreLevel,
    ScoreResult,
    StructuredResume,
)
from app.utils.ats_rules import STRONG_ACTION_VERBS, WEAK_VERBS
from app.utils.text_cleaning import has_metric, has_strong_verb

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────
_STRONG_VERBS_SET = set(v.lower() for v in STRONG_ACTION_VERBS)
_WEAK_VERBS_SET = set(v.lower() for v in WEAK_VERBS)
_EXPECTED_SECTIONS = {"summary", "education", "experience", "skills"}


def calculate_score(
    resume: StructuredResume,
    match_result: MatchResult,
) -> ScoreResult:
    """Main entry point: calculate the overall ATS compatibility score.

    Args:
        resume: Structured resume data.
        match_result: Output from the matcher service.

    Returns:
        ScoreResult with total score, level, and per-category breakdown.
    """
    categories: list[CategoryScore] = []

    # 1. Keyword Coverage (40%)
    kw_score = _score_keyword_coverage(match_result)
    categories.append(CategoryScore(
        name="Keyword Coverage",
        score=kw_score,
        weight=0.40,
        details=_keyword_detail(match_result, kw_score),
    ))

    # 2. Section Completeness (20%)
    sec_score = _score_section_completeness(resume)
    categories.append(CategoryScore(
        name="Section Completeness",
        score=sec_score,
        weight=0.20,
        details=_section_detail(resume, sec_score),
    ))

    # 3. Formatting Quality (15%)
    fmt_score = _score_formatting(match_result)
    categories.append(CategoryScore(
        name="Formatting Quality",
        score=fmt_score,
        weight=0.15,
        details=_formatting_detail(match_result, fmt_score),
    ))

    # 4. Action Verb Usage (15%)
    verb_score = _score_action_verbs(resume)
    categories.append(CategoryScore(
        name="Action Verb Usage",
        score=verb_score,
        weight=0.15,
        details=_verb_detail(resume, verb_score),
    ))

    # 5. Quantification (10%)
    quant_score = _score_quantification(resume)
    categories.append(CategoryScore(
        name="Quantification (Metrics)",
        score=quant_score,
        weight=0.10,
        details=_quantification_detail(resume, quant_score),
    ))

    # Weighted total
    total = sum(c.score * c.weight for c in categories)
    total = round(min(total, 100.0), 1)

    # Determine level
    if total >= 80:
        level = ScoreLevel.EXCELLENT
    elif total >= 60:
        level = ScoreLevel.GOOD
    elif total >= 40:
        level = ScoreLevel.FAIR
    else:
        level = ScoreLevel.POOR

    return ScoreResult(
        total_score=total,
        level=level,
        categories=categories,
        max_possible=100.0,
    )


# ── Category scoring functions ────────────────────────────


def _score_keyword_coverage(match: MatchResult) -> float:
    """Score keyword match percentage on a 0-100 scale.

    The raw match % maps linearly: higher match = higher score.
    A match of 0% yields a score floor of 10 (every resume has something).
    """
    if not match.matched_keywords and not match.missing_keywords:
        return 50.0  # No keywords to match — neutral score
    raw = match.keyword_match_pct
    # Floor at 10, cap at 100
    return max(10.0, min(100.0, raw))


def _score_section_completeness(resume: StructuredResume) -> float:
    """Score based on which expected sections are present.

    100 if all 4 core sections present, 0 if none.
    Points per section: summary=15, education=25, experience=35, skills=25
    """
    score = 0.0
    if resume.summary:
        score += 15
    if resume.education:
        score += 25
    if resume.experience:
        score += 35
    if resume.skills:
        score += 25
    return min(score, 100.0)


def _score_formatting(match: MatchResult) -> float:
    """Score formatting quality. Start at 100, deduct for issues."""
    score = 100.0
    for issue in match.formatting_issues:
        if issue.severity == "error":
            score -= 40
        elif issue.severity == "warning":
            score -= 20
        else:
            score -= 10
    return max(0.0, score)


def _score_action_verbs(resume: StructuredResume) -> float:
    """Score the ratio of strong verbs vs weak verbs in bullet points."""
    all_bullets = []
    for exp in resume.experience:
        all_bullets.extend(exp.bullets)
    for proj in resume.projects:
        if proj.description:  # approximate: treat project descriptions as bullets
            all_bullets.append(proj.description)

    if not all_bullets:
        return 50.0  # No bullets to evaluate — neutral middling score

    strong_count = sum(1 for b in all_bullets if b.has_strong_verb)
    weak_count = 0
    for b in all_bullets:
        first_word = b.text.strip().split()[0].lower().rstrip(".,;:") if b.text.strip() else ""
        if first_word in _WEAK_VERBS_SET:
            weak_count += 1

    ratio = strong_count / len(all_bullets)

    # Score mapping
    if ratio >= 0.7:
        return 100.0
    elif ratio >= 0.5:
        return 75.0
    elif ratio >= 0.3:
        return 50.0
    elif ratio >= 0.1:
        return 25.0
    else:
        return 10.0


def _score_quantification(resume: StructuredResume) -> float:
    """Score the presence of quantified metrics in experience bullets."""
    all_bullets = []
    for exp in resume.experience:
        all_bullets.extend(exp.bullets)

    if not all_bullets:
        return 0.0

    metric_count = sum(1 for b in all_bullets if b.has_metric)
    ratio = metric_count / len(all_bullets)

    if ratio >= 0.5:
        return 100.0
    elif ratio >= 0.3:
        return 70.0
    elif ratio >= 0.15:
        return 40.0
    elif ratio > 0:
        return 20.0
    else:
        return 0.0


# ── Detail descriptions (for UI transparency) ─────────────


def _keyword_detail(match: MatchResult, score: float) -> str:
    if not match.jd_provided:
        if score >= 80:
            return f"Strong coverage of common ATS keywords ({match.keyword_match_pct:.0f}%). "
            "Your resume includes most of the skills recruiters look for."
        elif score >= 50:
            return f"Moderate coverage ({match.keyword_match_pct:.0f}%). "
            f"Consider adding some of the missing keywords: {', '.join(match.missing_keywords[:5])}."
        else:
            return f"Low keyword coverage ({match.keyword_match_pct:.0f}%). "
            "Few common ATS keywords detected. Review the 'Missing Keywords' list below."
    else:
        if score >= 80:
            return f"Strong keyword alignment: {match.keyword_match_pct:.0f}% of JD keywords found."
        elif score >= 50:
            return f"Partial alignment ({match.keyword_match_pct:.0f}%). "
            f"Add these missing keywords: {', '.join(match.missing_keywords[:7])}."
        else:
            return f"Weak alignment ({match.keyword_match_pct:.0f}%). "
            "Your resume is missing most of the keywords mentioned in the job description."


def _section_detail(resume: StructuredResume, score: float) -> str:
    missing = []
    if not resume.summary:
        missing.append("Summary/Profile")
    if not resume.education:
        missing.append("Education")
    if not resume.experience:
        missing.append("Experience")
    if not resume.skills:
        missing.append("Skills")

    if not missing:
        return "All expected sections (Summary, Education, Experience, Skills) are present."
    else:
        return f"Missing sections: {', '.join(missing)}. Adding these improves ATS completeness by {20 - score:.0f} points."


def _formatting_detail(match: MatchResult, score: float) -> str:
    if not match.formatting_issues:
        return "No formatting issues detected. Your resume is ATS-friendly."
    else:
        issues = [f.issue_type.replace("_", " ").title() for f in match.formatting_issues]
        return f"Issues found: {', '.join(issues)}. These can cause ATS parsers to misread your content."


def _verb_detail(resume: StructuredResume, score: float) -> str:
    total_bullets = sum(len(exp.bullets) for exp in resume.experience)
    strong = sum(b.has_strong_verb for exp in resume.experience for b in exp.bullets)

    if total_bullets == 0:
        return "No bullet points found in experience section. Bullet points are standard for ATS parsing."

    if score >= 80:
        return f"Excellent use of action verbs: {strong}/{total_bullets} bullets start with strong verbs."
    elif score >= 50:
        return f"Decent verb usage: {strong}/{total_bullets} strong. Try replacing weak openings with impactful verbs."
    else:
        return f"Most bullets use weak openings ({strong}/{total_bullets} strong). "
        "Replace 'Was responsible for', 'Helped', 'Worked on' with action verbs like 'Led', 'Built', 'Optimized'."


def _quantification_detail(resume: StructuredResume, score: float) -> str:
    total_bullets = sum(len(exp.bullets) for exp in resume.experience)
    metrics = sum(b.has_metric for exp in resume.experience for b in exp.bullets)

    if total_bullets == 0:
        return "No bullet points to evaluate for metrics."

    if score >= 80:
        return f"Great use of metrics: {metrics}/{total_bullets} bullets include numbers, percentages, or dollar amounts."
    elif score >= 30:
        return f"Some metrics found ({metrics}/{total_bullets}). Adding more quantified results strengthens impact."
    else:
        return f"Few or no metrics found ({metrics}/{total_bullets}). "
        "Hiring managers respond strongly to numbers. Add percentages, dollar amounts, or time savings where possible."

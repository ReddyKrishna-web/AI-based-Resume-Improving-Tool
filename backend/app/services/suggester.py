"""
Suggestion engine — uses an LLM to generate specific, actionable rewrite
suggestions for weak bullet points.

Architectural decision: The LLM is ONLY used for qualitative suggestions.
The numeric score is purely rule-based (scorer.py). This separation:
1. Keeps the score deterministic and auditable.
2. Uses the LLM where it genuinely adds value — human-like phrasing advice.
3. Gracefully degrades if the API key is missing or the call fails.
4. Makes the system testable: unit-test the scoring, integration-test suggestions.

Prompt engineering note: The system prompt is kept concise and structured
to produce consistent JSON output. We request at most 5 suggestions to
keep the response focused and actionable.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from app.models.schemas import (
    ScoreResult,
    StructuredResume,
    Suggestion,
    SuggestionResult,
)

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────
DEFAULT_MODEL = "gpt-4o-mini"
MAX_SUGGESTIONS = 5


def generate_suggestions(
    resume: StructuredResume,
    score: ScoreResult,
    jd_text: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> SuggestionResult:
    """Generate suggestions for resume improvement using an LLM.

    Args:
        resume: Structured resume data.
        score: Score result (used to target weak areas).
        jd_text: Optional job description for contextual suggestions.
        api_key: OpenAI API key. Falls back to env var.
        model: OpenAI model name. Falls back to env var or default.

    Returns:
        SuggestionResult with suggestions (empty if API key missing or error).
    """
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    model_name = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    if not key:
        logger.warning("No OpenAI API key found — skipping LLM suggestions")
        return SuggestionResult(
            suggestions=[],
            generated=False,
            model_used=None,
        )

    prompt = _build_prompt(resume, score, jd_text)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert resume coach with deep knowledge of ATS "
                        "(Applicant Tracking System) optimization. Your task is to "
                        "analyze specific resume bullet points and suggest improvements. "
                        "\n\nFocus on:\n"
                        "1. Weak verbs → replace with strong action verbs\n"
                        "2. Missing metrics → add specific numbers, percentages, or timeframes\n"
                        "3. Vague impact → make the contribution explicit\n"
                        "4. Length → tighten overly verbose bullets\n"
                        "5. Relevance (if JD provided) → tailor to the target role\n\n"
                        "Return a JSON array of objects with keys: "
                        "section, original_text, suggestion, rationale. "
                        f"Maximum {MAX_SUGGESTIONS} suggestions. "
                        "Focus on the LOWEST-scoring areas first."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        raw_suggestions = data.get("suggestions", []) if isinstance(data, dict) else data
        suggestions = []
        for item in raw_suggestions[:MAX_SUGGESTIONS]:
            suggestions.append(Suggestion(
                section=item.get("section", "unknown"),
                original_text=item.get("original_text", ""),
                suggestion=item.get("suggestion", ""),
                rationale=item.get("rationale", ""),
            ))

        return SuggestionResult(
            suggestions=suggestions,
            generated=True,
            model_used=model_name,
        )

    except Exception as e:
        logger.error(f"LLM suggestion generation failed: {e}")
        return SuggestionResult(
            suggestions=[],
            generated=False,
            model_used=model_name,
        )


def _build_prompt(
    resume: StructuredResume,
    score: ScoreResult,
    jd_text: Optional[str] = None,
) -> str:
    """Build a structured prompt for the LLM.

    Includes the resume sections that need the most improvement
    (targeted by the lowest score categories).
    """
    parts: list[str] = []

    # Context
    parts.append("## Overall Score")
    parts.append(f"The resume scored {score.total_score}/100 ({score.level.value}).")
    parts.append("")

    # Low-scoring categories (these need suggestions)
    low_categories = [c for c in score.categories if c.score < 60]
    if low_categories:
        parts.append("## Areas Needing Improvement")
        for cat in low_categories:
            parts.append(f"- {cat.name}: {cat.score:.0f}/100 — {cat.details}")
        parts.append("")

    # Resume content (focused on experience bullets)
    parts.append("## Resume Content")
    for exp in resume.experience:
        parts.append(f"\n### {exp.title} at {exp.company}")
        for bullet in exp.bullets:
            parts.append(f"- {bullet.text}")

    for proj in resume.projects:
        parts.append(f"\n### Project: {proj.name}")
        if proj.description:
            parts.append(f"- {proj.description}")

    if resume.skills:
        parts.append(f"\n### Skills: {', '.join(resume.skills[:15])}")

    # JD context if available
    if jd_text:
        parts.append("\n## Target Job Description")
        parts.append(jd_text[:2000])  # Truncate to stay within token limits

    # Instructions
    parts.append(f"\n## Task")
    parts.append(
        f"Return a JSON object with a 'suggestions' key containing an array of "
        f"improvement suggestions (max {MAX_SUGGESTIONS}). Each suggestion must "
        f"have: 'section' (the resume section), 'original_text', 'suggestion', "
        f"and 'rationale'."
    )

    return "\n".join(parts)

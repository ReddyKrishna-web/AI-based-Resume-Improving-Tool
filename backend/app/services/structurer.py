"""
Resume structurer — converts raw extracted text into a structured
StructuredResume object with identified sections and extracted entities.

Architectural decision: Section detection uses regex-based heuristics
(not ML/LLM) for reproducibility and speed. The heading patterns in
ats_rules.py are the single source of truth, making the system easy
to extend with new section types.

Limitation: Non-English resumes may have section headers that don't
match our English patterns. We detect language and flag this.
"""

from __future__ import annotations

import logging
import re

from app.models.schemas import (
    BulletPoint,
    ContactInfo,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    StructuredResume,
)
from app.utils.ats_rules import SECTION_HEADINGS, STRONG_ACTION_VERBS
from app.utils.text_cleaning import (
    clean_line,
    detect_language,
    extract_emails,
    extract_phones,
    extract_urls,
    has_metric,
    has_strong_verb,
    normalize_whitespace,
    split_into_bullets,
)

logger = logging.getLogger(__name__)

# ── Compile heading regexes once ──────────────────────────
# Build a single combined regex pattern for all section headings
_HEADING_PATTERNS: dict[str, re.Pattern] = {}
for section, headings in SECTION_HEADINGS.items():
    # Match heading at start of line (possibly with leading whitespace)
    pattern = r"^\s*(?:" + "|".join(re.escape(h) for h in headings) + r")\s*:?\s*$"
    _HEADING_PATTERNS[section] = re.compile(pattern, re.IGNORECASE | re.MULTILINE)

# Combined pattern to find all section headers and their positions
_COMBINED_HEADING = re.compile(
    r"^\s*(?:" + "|".join(
        "|".join(re.escape(h) for h in headings)
        for headings in SECTION_HEADINGS.values()
    ) + r")\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_STRONG_VERBS_SET = set(v.lower() for v in STRONG_ACTION_VERBS)

# Title keywords for identifying job title vs company name
_TITLE_KEYWORDS = {
    "engineer", "developer", "manager", "analyst", "intern",
    "lead", "director", "head", "architect", "scientist",
    "consultant", "specialist", "coordinator", "associate",
}


def structure_resume(raw_text: str) -> StructuredResume:
    """Main entry point: convert raw text into a StructuredResume."""
    text = normalize_whitespace(raw_text)
    lines = text.split("\n")

    language = detect_language(text)

    contact = _extract_contact(text)
    sections = _split_into_sections(lines)

    summary = _parse_summary(sections.get("summary", []))
    education = _parse_education(sections.get("education", []))
    experience = _parse_experience(sections.get("experience", []), language)
    skills = _parse_skills(sections.get("skills", []))
    projects = _parse_projects(sections.get("projects", []), language)
    certifications = _parse_certifications(sections.get("certifications", []))

    return StructuredResume(
        contact=contact,
        summary=summary,
        education=education,
        experience=experience,
        skills=skills,
        projects=projects,
        certifications=certifications,
    )


# ── Internal helpers ──────────────────────────────────────


def _extract_contact(text: str) -> ContactInfo:
    """Extract contact information from the top of the resume."""
    emails = extract_emails(text)
    phones = extract_phones(text)
    urls = extract_urls(text)

    linkedin_url = ""
    for url in urls:
        if "linkedin" in url.lower():
            linkedin_url = url
            break

    # Location is typically near the top, often contains city/state
    # Heuristic: first few lines after stripping contact info
    lines = text.split("\n")[:10]
    location = ""
    for line in lines:
        line = line.strip()
        # Rough heuristic - contains words like city, state, or comma-separated location
        if re.search(r",\s*(?:ca|ny|tx|fl|il|wa|ma|co|ga|nc|va|or|az|mi|oh|pa|nj|mn|wi|md|in|tn|mo|ct|sc|al|ky|la|ok|or|ut|nv|ar|ms|ia|ks|ne|nm|id|wv|nd|sd|mt|wy|ak|hi|dc|ontario|british columbia|uk|london|berlin|paris|tokyo|sydney)", line, re.IGNORECASE):
            # Check it doesn't look like a job title
            if not any(kw in line.lower() for kw in ["engineer", "developer", "manager", "analyst", "scientist", "intern", "lead", "head of"]):
                location = line
                break

    return ContactInfo(
        email=emails[0] if emails else None,
        phone=phones[0] if phones else None,
        linkedin=linkedin_url or None,
        location=location or None,
    )


def _split_into_sections(lines: list[str]) -> dict[str, list[str]]:
    """Split resume text into sections based on heading patterns.

    Returns dict mapping section name -> list of content lines.
    """
    # Find all heading positions
    heading_positions: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        clean_line_text = clean_line(line)
        if not clean_line_text:
            continue
        match = _COMBINED_HEADING.match(line)
        if match:
            matched_text = match.group(0).strip().rstrip(":").strip().lower()
            # Map back to canonical section name
            for section, headings in SECTION_HEADINGS.items():
                if any(matched_text == h.lower() or matched_text.startswith(h.lower()) for h in headings):
                    heading_positions.append((i, section))
                    break

    if not heading_positions:
        # No sections found — return everything as raw "experience"
        logger.warning("No section headings detected — treating entire resume as content")
        return {}

    # Extract content between headings
    sections: dict[str, list[str]] = {}
    for idx, (start_pos, section_name) in enumerate(heading_positions):
        end_pos = heading_positions[idx + 1][0] if idx + 1 < len(heading_positions) else len(lines)
        content_lines = []
        for line in lines[start_pos + 1:end_pos]:
            cleaned = clean_line(line)
            if cleaned:
                content_lines.append(cleaned)
        sections[section_name] = content_lines

    return sections


def _parse_summary(lines: list[str]) -> str:
    """Summary/profile section is usually one or two paragraphs."""
    return " ".join(lines) if lines else ""


def _parse_education(lines: list[str]) -> list[EducationEntry]:
    """Parse education entries. Each entry typically spans 2-4 lines."""
    if not lines:
        return []

    entries: list[EducationEntry] = []
    current = EducationEntry()
    for line in lines:
        line_lower = line.lower()
        # Detect a new entry: starts with degree or institution name
        degrees = ["bachelor", "master", "phd", "doctorate", "associate",
                    "b.s.", "b.a.", "m.s.", "m.a.", "ph.d.", "b.eng", "m.eng",
                    "bachelor of", "master of", "doctor of"]
        if any(line_lower.startswith(d) for d in degrees):
            if current.institution or current.degree:
                entries.append(current)
            current = EducationEntry(degree=line)
        elif re.search(r"20\d{2}\s*(?:[-–to]|present|current)?\s*20\d{2}", line_lower):
            current.dates = (current.dates + " " + line).strip()
        else:
            if not current.institution:
                # Check if it looks like a university name
                if any(kw in line_lower for kw in ["university", "college", "institute", "school"]):
                    current.institution = line
                else:
                    current.field = (current.field + " " + line).strip()
            else:
                current.field = (current.field + " " + line).strip()

    if current.institution or current.degree:
        entries.append(current)

    return entries


def _parse_experience(lines: list[str], language: str) -> list[ExperienceEntry]:
    """Parse work experience entries with bullet points."""
    if not lines:
        return []

    entries: list[ExperienceEntry] = []
    current = ExperienceEntry()
    bullet_lines: list[str] = []

    for line in lines:
        # Check for company/job title line (often has comma or pipe separator)
        is_heading = False
        for sep in [" | ", "  —  ", "  –  ", "  -  ", " \\ ", "  |  "]:
            if sep in line:
                parts = line.split(sep)
                if len(parts) == 2:
                    is_heading = True
                    break

        if is_heading:
            # Save previous entry
            if current.company or current.title:
                current.bullets = _parse_bullets(bullet_lines, language)
                entries.append(current)
                bullet_lines = []
            current = ExperienceEntry()
            # Parse "Title | Company" or "Company | Title"
            parts = line.split(sep)
            # Heuristic: if one part contains typical title keywords, it's the title
            if any(kw in parts[0].lower() for kw in _TITLE_KEYWORDS):
                current.title = parts[0].strip()
                current.company = parts[1].strip()
            else:
                current.company = parts[0].strip()
                current.title = parts[1].strip()
        elif re.match(r"^\s*[•●◦‣⁃▪▸▹►›\-–*\d+[.)]\s]", line):
            bullet_lines.append(line)
        elif re.search(r"20\d{2}\s*(?:[-–to]|present|current)?", line.lower()):
            current.dates = (current.dates + " " + line).strip()
        else:
            # Could be company on its own line, or additional description
            if not current.company and not current.title:
                current.company = line
            elif not current.title:
                current.title = line
            else:
                # Extra description line — treat as a non-bullet note
                if line.strip():
                    bullet_lines.append(f"• {line.strip()}")

    # Save last entry
    if current.company or current.title:
        current.bullets = _parse_bullets(bullet_lines, language)
        entries.append(current)

    return entries


def _parse_bullets(lines: list[str], language: str) -> list[BulletPoint]:
    """Convert raw bullet lines into structured BulletPoint objects."""
    bullets: list[BulletPoint] = []
    for line in lines:
        # Strip leading bullet character/number
        text = re.sub(r"^\s*[•●◦‣⁃▪▸▹►›\-–*\d+[.)]\s*", "", line).strip()
        if text:
            bullets.append(BulletPoint(
                text=text,
                has_metric=has_metric(text),
                has_strong_verb=has_strong_verb(text, _STRONG_VERBS_SET),
            ))
    return bullets


def _parse_skills(lines: list[str]) -> list[str]:
    """Skills are often comma-separated or listed per-line."""
    skills: list[str] = []
    for line in lines:
        # Split on common separators
        parts = re.split(r"[,;|•]", line)
        for part in parts:
            part = part.strip().strip(".").strip()
            if part and len(part) > 1:
                skills.append(part)
    return skills


def _parse_projects(lines: list[str], language: str) -> list[ProjectEntry]:
    """Parse projects section."""
    if not lines:
        return []

    entries: list[ProjectEntry] = []
    current = ProjectEntry()
    tech_lines: list[str] = []

    for line in lines:
        # A project name often ends with a colon or is highlighted
        if line.endswith(":") or (line and not line.startswith("•") and not re.match(r"^\s*[\-–]", line)):
            if current.name:
                current.description = " ".join(tech_lines)
                entries.append(current)
                tech_lines = []
            current = ProjectEntry(name=line.rstrip(":"))
        elif line.startswith("•") or line.startswith("-"):
            tech_lines.append(line.lstrip("•-").strip())
        else:
            tech_lines.append(line)

    if current.name:
        current.description = " ".join(tech_lines)
        entries.append(current)

    return entries


def _parse_certifications(lines: list[str]) -> list[str]:
    """Certifications are typically one per line."""
    return [line.strip().strip("•- ") for line in lines if line.strip()]

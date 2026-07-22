"""
Pydantic schemas for the Resume Optimizer API.
These define the data contracts between services and the API response.
Key architectural decision: All service functions return these models,
keeping the HTTP layer (routers) thin and purely presentational.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


class ScoreLevel(str, Enum):
    EXCELLENT = "excellent"     # 80-100
    GOOD = "good"               # 60-79
    FAIR = "fair"               # 40-59
    POOR = "poor"               # 0-39


# ──────────────────────────────────────────────
# Nested / component models
# ──────────────────────────────────────────────

class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None


class EducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    dates: str = ""


class BulletPoint(BaseModel):
    text: str
    has_metric: bool = False
    has_strong_verb: bool = False
    suggestion: Optional[str] = None   # populated by LLM suggester


class ExperienceEntry(BaseModel):
    company: str = ""
    title: str = ""
    dates: str = ""
    bullets: list[BulletPoint] = []


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = []


class StructuredResume(BaseModel):
    """The fully parsed and structured resume."""
    contact: ContactInfo = ContactInfo()
    summary: str = ""
    education: list[EducationEntry] = []
    experience: list[ExperienceEntry] = []
    skills: list[str] = []
    projects: list[ProjectEntry] = []
    certifications: list[str] = []


# ──────────────────────────────────────────────
# Matching & scoring models
# ──────────────────────────────────────────────

class FormattingIssue(BaseModel):
    issue_type: str          # e.g. "multi_column", "table_detected", "scanned_pdf"
    severity: str            # "error", "warning", "info"
    message: str


class MatchResult(BaseModel):
    jd_provided: bool = False
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    keyword_match_pct: float = 0.0
    formatting_issues: list[FormattingIssue] = []


class CategoryScore(BaseModel):
    name: str
    score: float            # 0.0 – 100.0  (per category, normalised)
    weight: float           # 0.0 – 1.0   (contribution to total)
    details: str            # human-readable explanation


class ScoreResult(BaseModel):
    total_score: float = 0.0             # 0-100
    level: ScoreLevel = ScoreLevel.POOR
    categories: list[CategoryScore] = []
    max_possible: float = 100.0


# ──────────────────────────────────────────────
# Suggestion models
# ──────────────────────────────────────────────

class Suggestion(BaseModel):
    section: str                        # e.g. "experience"
    original_text: str
    suggestion: str
    rationale: str


class SuggestionResult(BaseModel):
    model_config = {"protected_namespaces": ()}
    suggestions: list[Suggestion] = []
    generated: bool = False             # whether LLM was actually called
    model_used: Optional[str] = None


# ──────────────────────────────────────────────
# Top-level request / response
# ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Payload when posting text directly (no file upload)."""
    resume_text: str = Field(..., description="Full resume text")
    jd_text: Optional[str] = Field(None, description="Target job description")


class AnalyzeResponse(BaseModel):
    """Complete analysis response returned to the frontend."""
    filename: str = ""
    file_type: Optional[FileType] = None
    structured: StructuredResume
    match: MatchResult
    score: ScoreResult
    suggestions: SuggestionResult
    warnings: list[str] = []             # high-level flags (scanned, multi-col, etc.)

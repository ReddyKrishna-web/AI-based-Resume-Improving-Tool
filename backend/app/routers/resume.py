"""
Resume analysis router — the single API endpoint that orchestrates
the entire pipeline.

POST /analyze  (multipart/form-data)
  - resume_file: PDF or DOCX file
  - jd_text: optional job description text

Returns AnalyzeResponse with structured resume, match data,
score breakdown, and suggestions.
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models.schemas import AnalyzeResponse, FormattingIssue
from app.services.matcher import analyze as match_resume
from app.services.parser import extract_text
from app.services.scorer import calculate_score
from app.services.structurer import structure_resume
from app.services.suggester import generate_suggestions
from app.utils.ats_rules import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["resume"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    resume_file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    jd_text: str = Form("", description="Optional job description text"),
):
    """Upload a resume (PDF/DOCX) and optionally a job description,
    receive a full ATS analysis with score breakdown and suggestions."""

    # ── 1. Validate file ──────────────────────────────────
    if resume_file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {resume_file.content_type}. "
                    "Only PDF and DOCX are supported.",
        )

    file_bytes = await resume_file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.",
        )

    filename = resume_file.filename or "resume.pdf"

    # ── 2. Parse (extract raw text) ────────────────────────
    try:
        parse_result = extract_text(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    if not parse_result.success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract text from this file. "
                   f"{' '.join(parse_result.warnings)}",
        )

    # ── 3. Structure (split into sections) ─────────────────
    structured = structure_resume(parse_result.raw_text)

    # ── 4. Match (keywords + formatting) ───────────────────
    match = match_resume(
        resume=structured,
        jd_text=jd_text if jd_text.strip() else None,
        formatting_warnings=parse_result.warnings,
    )

    # Add parser warnings as formatting issues
    for warning in parse_result.warnings:
        match.formatting_issues.append(
            FormattingIssue(
                issue_type="parser_warning",
                severity="warning",
                message=warning,
            )
        )

    # ── 5. Score (rule-based) ──────────────────────────────
    score = calculate_score(resume=structured, match_result=match)

    # ── 6. Suggest (LLM-based) ─────────────────────────────
    api_key = os.getenv("OPENAI_API_KEY", "")
    suggestions = generate_suggestions(
        resume=structured,
        score=score,
        jd_text=jd_text if jd_text.strip() else None,
        api_key=api_key if api_key else None,
    )

    # ── 7. Build response ──────────────────────────────────
    return AnalyzeResponse(
        filename=filename,
        file_type="pdf" if filename.lower().endswith(".pdf") else "docx",
        structured=structured,
        match=match,
        score=score,
        suggestions=suggestions,
        warnings=parse_result.warnings,
    )

"""
Resume Optimizer API — FastAPI application entry point.

Architecture notes:
- The API is served from a single process for simplicity (demo-appropriate).
- Static files (the React build) are served at `/` and `/assets/*`.
- The API routes are at `/api/*`.
- CORS is configured for development (localhost:5173) and production (same-origin).

In production, you'd likely put a reverse proxy (nginx, CloudFront) in front
and serve static assets separately, but for a demo this keeps deployment
to a single `uvicorn` command.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.resume import router as resume_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Optimizer API",
    version="1.0.0",
    description="AI-powered resume analysis and improvement tool. "
                "Upload a resume to get an ATS compatibility score, "
                "keyword gap analysis, and specific rewrite suggestions.",
)

# ── CORS (allow Vite dev server) ─────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev
        "http://localhost:3000",    # alternative dev port
        "http://localhost:8000",    # same-origin via static serving
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────
app.include_router(resume_router)

# ── Static file serving (for the built React frontend) ───
frontend_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    logger.info(f"Serving frontend from {frontend_dir}")
else:
    logger.info(
        "No frontend build found at %s. "
        "The API is running — serve the frontend separately with `npm run dev` in frontend/.",
        frontend_dir,
    )


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

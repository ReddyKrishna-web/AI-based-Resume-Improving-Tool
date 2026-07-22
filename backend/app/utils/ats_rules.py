"""
ATS ruleset — deterministic keyword banks for common resume domains.
Used when no job description is provided by the user.

Architectural decision: Hardcoded keyword lists are transparent, auditable,
and run offline. This is deliberately NOT an AI-generated set, so the
scoring is reproducible and explainable in an interview setting.
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────
# Generic ATS keywords (used when no JD is provided)
# These represent skills recruiters commonly search for.
# ──────────────────────────────────────────────────────────

GENERAL_SKILLS: list[str] = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
    "rust", "swift", "kotlin", "scala", "php", "sql", "bash", "shell",
    "r", "matlab", "perl", "dart", "lua",
    # Web frameworks
    "react", "angular", "vue", "django", "flask", "fastapi", "spring",
    "rails", "express", "node.js", "next.js", "svelte", "tailwind",
    "bootstrap", "jquery", "asp.net", "laravel", "symfony",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
    "cassandra", "oracle", "sqlite", "mariadb", "firebase", "supabase",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform",
    "ansible", "ci/cd", "github actions", "gitlab ci", "pulumi",
    # Data & ML
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "pandas", "numpy", "scikit-learn", "spark", "hadoop", "sql",
    "data pipeline", "etl", "airflow", "dbt", "tableau", "power bi",
    # Tools & practices
    "git", "linux", "agile", "scrum", "jira", "confluence", "rest api",
    "graphql", "microservices", "tdd", "unit testing", "ci/cd",
]

# ──────────────────────────────────────────────────────────
# Strong action verbs (for bullet-point scoring)
# Weak verbs like "was responsible for" or "helped" get flagged.
# ──────────────────────────────────────────────────────────

STRONG_ACTION_VERBS: list[str] = [
    "achieved", "accelerated", "architected", "automated", "built",
    "championed", "consolidated", "created", "cut", "debugged",
    "decreased", "delivered", "deployed", "designed", "developed",
    "doubled", "drove", "eliminated", "enabled", "engineered",
    "established", "exceeded", "executed", "expanded", "generated",
    "grew", "identified", "implemented", "improved", "increased",
    "initiated", "integrated", "introduced", "launched", "led",
    "mentored", "migrated", "negotiated", "optimized", "orchestrated",
    "overhauled", "pioneered", "proposed", "proved", "quadrupled",
    "rearchitected", "reduced", "reengineered", "refactored",
    "reorganized", "replaced", "resolved", "restructured", "revamped",
    "scaled", "simplified", "slashed", "solved", "spearheaded",
    "standardized", "streamlined", "strengthened", "transformed",
    "tripled", "upgraded", "won",
]

# ──────────────────────────────────────────────────────────
# Weak / generic verbs that indicate a bullet needs rewriting
# ──────────────────────────────────────────────────────────

WEAK_VERBS: list[str] = [
    "was", "were", "has", "have", "had", "did", "made", "got",
    "helped", "worked on", "worked with", "responsible for",
    "tasked with", "participated", "involved in", "assisted",
    "served as", "acted as", "was part of",
]

# ──────────────────────────────────────────────────────────
# Section heading patterns (case-insensitive regex)
# ──────────────────────────────────────────────────────────

SECTION_HEADINGS: dict[str, list[str]] = {
    "summary": [
        "summary", "professional summary", "profile", "about me",
        "career objective", "objective",
    ],
    "education": [
        "education", "academic background", "academic history",
        "qualifications", "educational qualifications",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment", "work history", "relevant experience",
        "career history", "professional background",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "technologies", "expertise", "technical expertise",
        "key skills", "competencies", "proficiencies",
    ],
    "projects": [
        "projects", "project experience", "key projects",
        "personal projects", "academic projects",
    ],
    "certifications": [
        "certifications", "certificates", "licenses",
        "professional certifications", "accreditations",
    ],
}

# ──────────────────────────────────────────────────────────
# File size limits
# ──────────────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

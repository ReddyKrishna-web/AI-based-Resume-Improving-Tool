# Resume Optimizer — AI-Powered ATS Analysis Tool

A portfolio project demonstrating a well-architected AI application: resume parsing, ATS scoring, and actionable improvement suggestions.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) OpenAI API key for LLM-powered suggestions

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Optional: enable LLM suggestions
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.
Try it: `POST /api/analyze` with a resume file, or visit `http://localhost:8000/docs` for Swagger UI.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:5173`. The Vite dev server proxies `/api/*` to the backend.

> **One-command production**: `cd frontend && npm run build` then serve from the backend —
> FastAPI automatically serves the built frontend from `frontend/dist/`.

---

## Pipeline Architecture

```
[User Upload] → [Parser] → [Structurer] → [Matcher] → [Scorer] → [Suggester] → [Results]
```

Each stage is a pure function with a single responsibility. Here's what each does:

### 1. Parser (`backend/app/services/parser.py`)
**Input:** Raw file bytes (PDF or DOCX)
**Output:** Raw text + metadata (page count, multi-column flag, scanned flag)

- Uses **PyMuPDF (fitz)** for PDFs — chosen over PyPDF2/pdfplumber because it provides character-level bounding-box coordinates, which we need for multi-column detection.
- Uses **python-docx** for DOCX files — the standard library.
- **Multi-column detection** works by analyzing x-coordinate clusters of text blocks. If blocks split into two distinct horizontal ranges, we flag it rather than trying to reconstruct reading order (a hard NLP problem).
- **Scanned PDF detection**: if PyMuPDF extracts <10 characters, we return a clear "this is a scanned image" error instead of silently failing.

### 2. Structurer (`backend/app/services/structurer.py`)
**Input:** Raw text
**Output:** StructuredResume (contact, education, experience, skills, projects, certifications)

- Uses **regex-based section heading detection** — the section patterns in `ats_rules.py` are the single source of truth.
- Contact info extraction uses regex patterns for email, phone, URL, and location.
- Experience parsing handles common resume formats: "Title | Company", "Company – Title", bullet-point indicators.
- Language detection uses a simple ASCII ratio — enough to warn non-English users.

### 3. Matcher (`backend/app/services/matcher.py`)
**Input:** StructuredResume + optional job description text
**Output:** MatchResult (matched/missing keywords, keyword match %, formatting issues)

- Two modes:
  - **JD provided**: Extracts keywords from the job description using capitalized-phrase detection and skill-bank matching, then compares against resume.
  - **No JD**: Falls back to a hardcoded bank of ~100 common ATS keywords from `ats_rules.py`.
- **Fuzzy matching**: A keyword "matches" if it's a substring of any resume word/term. This catches "PostgreSQL" vs "Postgres" without complex NLP.

### 4. Scorer (`backend/app/services/scorer.py`)
**Input:** StructuredResume + MatchResult
**Output:** ScoreResult (total 0-100 + per-category breakdown)

**This is the most architecturally important component. It is 100% rule-based.**

| Category | Weight | What It Measures |
|---|---|---|
| Keyword Coverage | 40% | % of required/generic keywords found |
| Section Completeness | 20% | Are Summary, Education, Experience, Skills present? |
| Formatting Quality | 15% | Penalties for tables, images, long lines, special chars |
| Action Verb Usage | 15% | Ratio of strong verbs (Led, Built) to weak (Was, Helped) |
| Quantification | 10% | % of bullets containing numbers, metrics, or dollar amounts |

Each category produces a 0-100 score with a human-readable explanation string. The weighted sum gives the final score.

### 5. Suggester (`backend/app/services/suggester.py`)
**Input:** StructuredResume + ScoreResult + optional JD
**Output:** SuggestionResult (up to 5 specific rewrite suggestions)

- **This is the ONLY AI-powered component.** It uses `gpt-4o-mini` (configurable) to generate specific rewrite suggestions for weak bullet points.
- The prompt is structured JSON-only, targeting the lowest-scoring categories.
- **Graceful degradation**: If no API key is set or the API call fails, returns an empty list with `generated=False`. The frontend shows a helpful message instead of crashing.
- **Why only here?** Because qualitative text improvement genuinely benefits from language understanding. The numeric score should be deterministic and auditable — an interview panel would rightly question "Why did my score change between runs?" if AI was involved in scoring.

---

## Key Design Decisions (Interview Talking Points)

### "Why not use AI for everything?"

AI is excellent at fuzzy, qualitative tasks (rewriting, suggestions) but poor at transparent, reproducible scoring. By using rule-based scoring:
- **The score is deterministic** — same resume always gets the same score
- **Every point is explainable** — each category has a plain-English reason
- **No API cost for scoring** — runs fully offline
- **Testable** — the test file `test_scorer.py` proves specific inputs produce specific outputs

The LLM is only invoked for the suggestion step, where its language understanding genuinely adds value.

### "How do you handle edge cases?"

Three explicitly identified edge cases are handled by detection + graceful degradation:

1. **Multi-column PDFs** → detected by x-coordinate clustering → flagged as a warning → text still processed (keywords still match, though order may be jumbled)
2. **Scanned PDFs** → detected by zero-text extraction → returns 422 with clear error + remediation suggestion
3. **Non-English resumes** → detected by ASCII character ratio → still processed with reduced keyword weight + explicit note

The principle: detect early, fail gracefully, tell the user why.

### "How would you scale this?"

- Each service is a stateless function → easily parallelized
- The parser is the bottleneck (file I/O + PyMuPDF) → could be moved to a background task queue
- LLM suggestions are the most expensive → could be cached (same resume = same suggestions) or batched

---

## Edge Cases We Don't Handle (Honest Limitations)

| Edge Case | Why Not | Workaround |
|---|---|---|
| **Image-only PDFs** (scanned) | OCR is a heavy system dependency (Tesseract is 200MB+) | Clear error message suggesting OCR tools |
| **Complex multi-column reconstruction** | Active research area; no reliable heuristic | Flag + suggest single-column format |
| **Non-English scoring** | Keyword bank is English-only | Detect language + warn user |
| **Handwritten resumes** | Beyond scope | Not supported |

This honesty demonstrates good engineering judgment — knowing when to handle vs. when to communicate a limitation.

---

## Project Structure

```
resume-optimizer/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry, static serving
│   │   ├── models/schemas.py       # Pydantic data contracts
│   │   ├── routers/resume.py       # POST /api/analyze
│   │   ├── services/
│   │   │   ├── parser.py           # PDF/DOCX text extraction
│   │   │   ├── structurer.py       # Section identification
│   │   │   ├── matcher.py          # Keyword matching
│   │   │   ├── scorer.py           # Score calculation (rule-based)
│   │   │   └── suggester.py        # LLM suggestions
│   │   └── utils/
│   │       ├── ats_rules.py        # Keyword bank, verb lists
│   │       └── text_cleaning.py    # Normalization helpers
│   ├── tests/                      # pytest unit tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── api/client.ts           # Fetch wrapper
│   │   └── types/index.ts          # TypeScript interfaces
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── .gitignore
└── README.md
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | No | — | Enables LLM rewrite suggestions |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for suggestions |
| `HOST` | No | `0.0.0.0` | Backend server host |
| `PORT` | No | `8000` | Backend server port |

## License

MIT — free for portfolio use and personal projects.

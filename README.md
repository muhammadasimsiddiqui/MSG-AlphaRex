# SkillSprint AI

SkillSprint AI converts approved organizational documents into traceable, role-specific onboarding plans. A GenAI service generates structured JSON. A separate deterministic Python pipeline verifies it against immutable source evidence and the Role Requirement Matrix before approval.

## Run Locally

1. Create a virtual environment and run `pip install -r requirements.txt` from the repository root.
2. Copy `.env.example` to `.env`. Set a strong `JWT_SECRET`; set `OPENAI_API_KEY` and `OPENAI_MODEL` to enable live generation. Set `GENERATION_MODE=mock` to use the offline deterministic generator instead.
3. From `backend`, run `python -m app.seed --reset` to create the Northstar Field Services evaluation pack.
4. From `backend`, run `uvicorn app.main:app --reload`.
5. From `frontend`, run `npm install` then `npm run dev`.

Seeded test accounts (password `ChangeMe123!` for all — locally only; replace or disable before going to production): `admin@skillsprint.local` (System Administrator), `reviewer@skillsprint.local` (Quality Reviewer), `training@skillsprint.local` (Training Manager), `manager@skillsprint.local` (Department Manager), `learner@skillsprint.local` (Demo Learner, linked to employee profile `NSF-E001`). Each role sees its own dashboard and tabs: admin sees everything; training manager handles knowledge/matrix/plan generation/reports; reviewer validates and approves plans; manager sees overview and employees; learner gets a personal onboarding dashboard with modules, progress and source evidence. API documentation is at `http://127.0.0.1:8000/docs`.

## Core Controls

- PDF and DOCX validation, parsing, chunking, metadata, content hashes, and active/obsolete version status.
- Immutable citations: every matrix requirement stores document ID, version, section, and chunk ID.
- Quarantine for documents containing suspicious prompt-injection patterns. Quarantined content cannot be used for requirements or retrieval.
- Versioned prompt template and OpenAI JSON-schema generation with two bounded retries.
- Independent Python validation checks mandatory coverage, citations, role, mandatory flag, priority, duplicates, and prerequisite sequence. It never calls a GenAI model.
- JWT authentication with RBAC for administrator, training manager, reviewer, manager, and employee roles.
- Persisted plans, validation records, review decisions, audit events, impact analysis, dashboard metrics, and CSV exports.

## Project Layout

- `backend/app/services/`: ingestion, retrieval, generation, validation, and audit services.
- `backend/prompt_templates/`: controlled prompt versions.
- `backend/app/seed.py`: reproducible fictional-company dataset generator.
- `frontend/`: React JSX and Vite interface.
- `documentation/`: evaluator guide, architecture, and security model.
- `sample_documents/`: generated Northstar dataset after the seed command runs.

## Verification

Run `python -m pytest` from `backend` and `npm run build` from `frontend`.

## Generation Modes

- `GENERATION_MODE=auto` with a configured, credited `OPENAI_API_KEY` calls OpenAI structured output against the versioned prompt template and approved evidence. A valid key with exhausted credits raises a clear `402` instead of fabricating content.
- `GENERATION_MODE=mock` (default) builds deterministic plans from the approved matrix and evidence chunks. This exercises the validation, review, approval, and audit workflows offline. Both paths feed the same independent Python validation pipeline.

## Limitations

The seed pack uses DOCX fixtures. The application parses both PDF and DOCX, but scanned PDFs need an OCR provider, which is intentionally not bundled. Live content generation requires a funded, configured OpenAI account; the mock generator keeps the rest of the platform fully testable without one.

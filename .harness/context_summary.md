# Context Summary

Persistent record of architectural decisions, discovered patterns, gotchas, and active context.
This file is referenced in CLAUDE.md and loaded every session.

## Active Context
- Currently working on: F001 completed; next is F002 (document chunking and embedding pipeline)
- Backend structure established under `readflow/api/app/`
- Harness full_test green: 15 tests passing, 98% coverage on touched code

## Cross-Cutting Concerns
- Stack: Python/FastAPI (web backend), web frontend (to be decided)
- Architecture: AI + RAG assisted PDF reading tool
- Key constraints: web-based interaction; PDF upload/parse; retrieval Q&A over documents
- Root `pyproject.toml` duplicates backend deps so `.harness/init.sh` can run from repo root

## Domain: AI-Assisted Document Reading

### Decisions
- Python/FastAPI chosen as primary stack for PDF parsing, embedding, and retrieval Q&A (2026-06-29)
- Git identity: xliCoder <primeshift@163.com> via github.com SSH
- Project structure follows `CLAUDE.md` `readflow/api/app/` layout, not the generic `src/` paths in initial `features.json` (updated F001 scope)
- SQLAlchemy 2.0 async with `asyncpg` for PostgreSQL; tests use `sqlite+aiosqlite:///:memory:` via dependency override
- PDF parsing uses `pypdf` wrapped in `asyncio.to_thread` to keep IO async-compliant
- `ContentSource.status` state machine: `pending` -> `parsed` -> `chunked` -> `indexed` -> `failed`; F001 sets `parsed`
- Pydantic response schema uses `validation_alias='id'` to map ORM `id` to API field `source_id` without serializing as `id`

### Patterns
- Service layer: `app/services/pdf_service.py` exposes async methods; future services (chunking, embedding) follow same pattern
- Dependency injection: `get_db_session()` yields async sessions; tests override with in-memory session
- TDD fixture for binary assets: use `reportlab` to generate PDF bytes in-memory instead of committing binary files

### Gotchas
- Black's default string normalization converts single quotes to double; set `skip-string-normalization = true` in `pyproject.toml` to honor CLAUDE.md single-quote style
- Coverage on `routers/content.py` lines 43-45 is reported as missed despite the success path being exercised; this appears to be a coverage/AsyncFastAPI line-tracking quirk and does not affect the 95% gate
- `make` is not available in this Windows environment; root `pyproject.toml` is used as the harness entry point instead of `Makefile`

## Meta-Session 2026-07-01
- Scope accuracy: F001 scope in `features.json` was initialized with `src/upload/`, `src/pdf/` which did not match `CLAUDE.md`. Updated at start of implementation. Future sessions should reconcile `features.json` scope with actual architecture before spawning teammates.
- Model calibration: Single-session implementation on Opus worked well for the first feature because it involved project structure setup and architectural decisions. For F002-F005, continue single-session until a feature is clearly parallelizable.
- Discovery lineage: No new features discovered during F001.
- Approach patterns: TDD with failing tests first caught the `source_id`/`id` serialization issue early. `reportlab` fixtures avoided binary test assets.
- Plan approval: Not used (single-session). Plan mode was valuable for getting alignment on project structure before coding in an empty repo.

## Meta-Patterns
- For empty-repo first features, plan mode + single-session is safer than Agent Teams because scope and directory structure are still stabilizing.
- When `CLAUDE.md` structure and `features.json` scopes mismatch, update `features.json` before implementation to keep harness tracking accurate.
- Keep a root `pyproject.toml` that mirrors backend deps so harness init.sh can run tests without requiring `make`/Makefile on Windows.

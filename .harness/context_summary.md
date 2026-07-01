# Context Summary

Persistent record of architectural decisions, discovered patterns, gotchas, and active context.
This file is referenced in CLAUDE.md and loaded every session.

## Active Context
- Currently working on: F002 completed; next is F003 (retrieval Q&A API endpoint)
- Backend structure established under `readflow/api/app/`
- Harness full_test green: 38 tests passing, 100% coverage on touched code

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
- `ContentSource.status` state machine: `pending` -> `parsed` -> `chunked` -> `indexed` -> `failed`; F001 sets `parsed`, F002 sets `indexed`
- Pydantic response schema uses `validation_alias='id'` to map ORM `id` to API field `source_id` without serializing as `id`
- F002 extends F001 by persisting full `extracted_text` in `ContentSource` so chunking can operate without re-parsing the PDF bytes
- Chunking strategy: recursive-character splitting with paragraph -> sentence -> word -> character fallback, configurable `chunk_size` and `chunk_overlap`
- One API embedding client uses `httpx.AsyncClient` and standard `/v1/embeddings` OpenAI-compatible endpoint
- Vector storage uses `pymilvus.MilvusClient` with lazy collection creation; collection schema uses `source_id` partition key implicitly by filtering

### Patterns
- Service layer: `app/services/pdf_service.py` exposes async methods; future services (chunking, embedding) follow same pattern
- Dependency injection: `get_db_session()` yields async sessions; tests override with in-memory session
- TDD fixture for binary assets: use `reportlab` to generate PDF bytes in-memory instead of committing binary files
- Core clients live in `app/core/` (one_api_client, future milvus/redis/rabbitmq clients)
- Endpoint orchestration: router handlers coordinate services and translate domain exceptions to HTTP status codes; keep business logic in services
- Mock external IO in tests: patch `one_api_client.embed` and `vector_service.insert_chunks` for fast, deterministic integration tests

### Gotchas
- Black's default string normalization converts single quotes to double; set `skip-string-normalization = true` in `pyproject.toml` to honor CLAUDE.md single-quote style
- Coverage on FastAPI async routes requires `coverage.run.concurrency = ['thread', 'greenlet']`; without it, coverage misses many executed lines in `routers/content.py`
- `make` is not available in this Windows environment; root `pyproject.toml` is used as the harness entry point instead of `Makefile`
- `.harness/init.sh` returns exit code 49 on Windows Git Bash even though the underlying `pytest` invocation succeeds; direct `pytest` is the reliable test command
- `pymilvus` install emits a setuptools conflict warning from `torch` (unrelated to this project); pip install succeeds and functionality is unaffected

## Meta-Session 2026-07-01
- Scope accuracy: F001 scope in `features.json` was initialized with `src/upload/`, `src/pdf/` which did not match `CLAUDE.md`. Updated at start of implementation. F002 scope also had generic `src/indexing/` paths; realigned to `readflow/api/app/` before coding.
- Model calibration: Single-session implementation on Opus worked well for F001 (structural setup) and F002 (cross-service integration). No need for Agent Teams yet.
- Discovery lineage: F002 discovered that F001 must persist full `extracted_text` (not just preview) for chunking. This was folded into F002 scope rather than spawning a new feature.
- Approach patterns: TDD with failing tests first caught the `source_id`/`id` serialization issue early. `reportlab` fixtures avoided binary test assets. Recursive-character chunking with paragraph priority produced clean, semantically coherent chunks. Mocking `one_api_client.embed` and `vector_service.insert_chunks` kept integration tests fast and deterministic.
- Plan approval: Not used (single-session). Plan mode was valuable for getting alignment on project structure before coding in an empty repo.
- Coverage tooling: FastAPI async route coverage is unreliable without `coverage.run.concurrency = ['thread', 'greenlet']`. After adding this, coverage jumped from ~88% to 100% with no code changes. Documented as a gotcha for future sessions.

## Meta-Patterns
- For empty-repo first features, plan mode + single-session is safer than Agent Teams because scope and directory structure are still stabilizing.
- When `CLAUDE.md` structure and `features.json` scopes mismatch, update `features.json` before implementation to keep harness tracking accurate.
- Keep a root `pyproject.toml` that mirrors backend deps so harness init.sh can run tests without requiring `make`/Makefile on Windows.

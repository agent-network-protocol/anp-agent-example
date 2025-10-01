# Repository Guidelines

## Project Structure & Module Organization
- `example_code/` holds FastAPI routers consumed by downstream services; keep each router scoped to a single protocol concern.
- `example_code/api/` stores JSON and YAML artifacts surfaced by `api_router.py` and `yaml_router.py`; validate changes before merging.
- `example_code/ad_router.py` is the canonical source for ANP agent metadata; coordinate updates with dependent clients.
- `tests/` mirrors the runtime package layout; add new suites alongside the modules they exercise.

## Build, Test, and Development Commands
- `uv sync` installs or refreshes dependencies defined in `pyproject.toml`.
- `uv run pytest` executes the full automated test suite; add `-k <expr>` to narrow scope when iterating.
- `uv run ruff check example_code tests` enforces import hygiene and Google-style formatting expectations.
- `uv run python -m http.server --directory example_code/api 9000` offers a quick smoke test for static interface assets.

## Coding Style & Naming Conventions
- Follow the Google Python Style Guide: four-space indentation, snake_case modules and functions, PascalCase classes.
- Add type hints and concise docstrings describing router responsibilities; keep comments and logs in English.
- Use module-level `logger = logging.getLogger(__name__)`; avoid printing directly to stdout.

## Testing Guidelines
- Prefer `pytest` with `pytest-asyncio` and `httpx.AsyncClient` when exercising async endpoints.
- Target ≥85% statement coverage on touched modules and document any intentional gaps.
- Name tests after the behavior under inspection (e.g., `test_yaml_router_handles_invalid_payload`).

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat: add yaml router validation`) with subjects ≤72 characters.
- Summaries must capture scope, testing evidence (`uv run pytest`, lint results), and sample payload changes when interfaces shift.
- Link issues or RFCs, request at least one maintainer review, and document new configuration requirements.

## Security & Configuration Tips
- Keep secrets out of the repository; store local overrides in ignored `.env` files.
- `auth_middleware` expects environment-specific key paths—verify settings across environments before deployment.
- Validate modified JSON/YAML artifacts against provided schemas to avoid breaking dependent agents.

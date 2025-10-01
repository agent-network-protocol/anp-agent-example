# Repository Guidelines

## Project Structure & Module Organization
- `example_code/` stores FastAPI routers consumed by downstream services; keep each router focused on a single protocol concern.
- `example_code/ad_router.py` is the source of truth for ANP agent metadata, while `api_router.py` and `yaml_router.py` expose JSON/YAML artifacts from `example_code/api/`.
- `auth_middleware.py` integrates DidWbaVerifier without leaking framework specifics; extend it by adding helpers rather than inlining complex logic inside handlers.

## Build, Test, and Development Commands
- `uv sync` installs or refreshes dependencies listed in `pyproject.toml`.
- `uv run pytest` runs the full automated test suite; add `-k <expr>` to scope a run.
- `uv run ruff check example_code tests` enforces lint and import hygiene; fix issues before requesting review.
- Static assets can be smoke-tested with `uv run python -m http.server --directory example_code/api 9000` after editing interface files.

## Coding Style & Naming Conventions
- Follow the Google Python Style Guide with four-space indentation, snake_case for functions/modules, and PascalCase for classes.
- Add type hints and concise docstrings explaining router responsibilities; keep comments and logs in English.
- Use module-level `logger = logging.getLogger(__name__)` and avoid printing directly to stdout.
- When adding new routers, group validation helpers in private functions to keep request handlers short and testable.

## Testing Guidelines
- Place tests under `tests/`, mirroring the package you exercise (e.g., `tests/api/test_ad_router.py`).
- Prefer `pytest` with `pytest-asyncio` and `httpx.AsyncClient` for async endpoints; include regression tests for bug fixes touching protocol documents.
- Aim for ≥85% statement coverage on touched modules and document any intentional gaps in the pull request description.

## Commit & Pull Request Guidelines
- Git history is currently minimal (`Initial commit`); adopt Conventional Commits (`feat:`, `fix:`, `docs:`) to convey intent.
- Keep commit subject lines ≤72 characters and squash noisy work-in-progress commits before opening a pull request.
- Pull requests must detail scope, testing evidence (`uv run pytest`, lint results), and provide sample payloads when router responses change.
- Link issues or RFCs, request at least one maintainer review, and ensure new configuration requirements are documented.

## Security & Configuration Tips
- `auth_middleware` expects key paths provided by environment-specific settings; never commit secrets and store local overrides in ignored `.env` files.
- Validate modified JSON/YAML artifacts against their schemas before merge to prevent breaking dependent agents.

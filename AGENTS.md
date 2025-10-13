# Repository Guidelines

## Project Structure & Module Organization
The agent lives in `src/`; `main.py` bootstraps the FastAPI runtime, `config.py` centralizes environment-dependent defaults, and `api/` holds exported schemas such as `external-interface.json`. Feature modules stay close to the routing layer they serve, while shared utilities belong in `src/shared/` (create the directory if needed) to keep imports predictable. Place runnable samples and payloads under `examples/` and keep them minimal so `uv run` executions stay fast. Update `docs/` when public contracts or architecture touchpoints change. Tests mirror the runtime in `tests/unit/` and `tests/integration/`, letting contributors spot coverage gaps quickly.

## Build, Test, and Development Commands
Run `uv sync` whenever dependencies change to refresh the resolver-managed environment. Use `uv run python src/main.py` for the default development server, and add `--reload` while iterating on handlers. Execute `uv run pytest` for the full suite; scope work with `-k` or `tests/unit/` when triaging failures. Lint before pushing with `uv run ruff check src tests`, and format fixes via `uv run ruff format`.

## Coding Style & Naming Conventions
Follow Google Python Style: four-space indentation, snake_case functions, PascalCase classes, and explicit type hints on public call sites. Keep module docstrings concise, focusing on business context instead of implementation details. Instantiate loggers as `logger = logging.getLogger(__name__)` and emit structured, English messages. Configuration constants belong in `config.py`; import them rather than duplicating literals.

## Testing Guidelines
Rely on `pytest` and `pytest-asyncio` for async endpoints, using `httpx.AsyncClient` fixtures to avoid brittle sleeps. Name tests after observable behavior, for example `test_main_starts_http_server`. Maintain at least 85% coverage on touched modules; document exceptions in the pull request. Mark slower cross-system checks with `@pytest.mark.integration` so CI can segment workloads.

## Commit & Pull Request Guidelines
Write Conventional Commit messages such as `feat: add scheduler hook`, keeping subjects under 72 characters and imperative. Reference related issues or RFCs in the body, list validation evidence (`uv run pytest`, `uv run ruff check`), and attach sample requests when API payloads shift. Pull requests should describe rollout risks, config toggles, and any manual follow-up required for deployment.

## Security & Configuration Tips
Copy `env.example` to `.env` for local overrides and keep secrets out of version control. Validate JSON artifacts in `src/api/` against consumer expectations before merging. Confirm authentication keys and third-party URLs through `config.py` and avoid hard-coding environment-specific paths.

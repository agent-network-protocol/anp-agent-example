# Repository Guidelines

## Project Structure & Module Organization
Runtime code sits in `src/`. `remote_agent.py` hosts the FastANP-powered server, while `local_agent.py` and `local_agent_use_llm.py` demonstrate scripted and LLM-assisted clients. Keep shared helpers alongside their consumers; extract only widely reused logic into `src/shared/` when duplication emerges. Configuration defaults live in `src/config.py`. Sample payloads and walkthrough scripts belong in `examples/`, and reusable DID or key artifacts stay under `docs/did_public/` and `docs/jwt_key/`. Place new tests in `tests/unit/` or `tests/integration/` to mirror the runtime layout.

## Build, Test, and Development Commands
Run `uv sync` whenever `pyproject.toml` or `uv.lock` changes to refresh dependencies. Start the remote agent locally with `PYTHONPATH=src uv run python src/remote_agent.py`; add `--reload` while iterating. Validate the scripted clients using `uv run python run_example.py`, `PYTHONPATH=src uv run python src/local_agent.py`, and `PYTHONPATH=src uv run python src/local_agent_use_llm.py`. Execute `uv run pytest` for automated tests, `uv run ruff check src tests` for linting, and `uv run ruff format` to apply formatting fixes.

## Coding Style & Naming Conventions
Follow Google Python Style: four-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and explicit type hints on public call sites. Favor descriptive docstrings that explain intent, not implementation minutiae. Loggers should be declared as `logger = logging.getLogger(__name__)` and emit concise English messages. Store configuration constants in `config.py`; import them rather than duplicating literals.

## Testing Guidelines
Adopt `pytest` (with `pytest-asyncio` when needed) for all automated coverage. Name test files after the module under test (`test_remote_agent.py`) and test functions after observable behavior (`test_greet_returns_personalized_message`). Maintain at least 85% line coverage across touched modules; document any justified exceptions in the pull request. Use `@pytest.mark.integration` for cross-service checks so suites can be filtered (`uv run pytest -k integration`).

## Commit & Pull Request Guidelines
Use Conventional Commits (`feat:`, `fix:`, `chore:`) with imperative, ≤72-character subjects. Reference related issues or RFCs in the body and include validation evidence such as `uv run pytest` and `uv run ruff check`. Pull requests must summarize functional changes, note any configuration toggles, list manual follow-up steps, and attach sample ANP requests if API contracts shift.

## Security & Configuration Tips
Copy `env.example` to `.env` before running locally, updating domains, key paths, and token lifetimes to match your environment. Keep private keys outside version control; if replacements are required, update `docs/jwt_key/` and `config.py` consistently. When publishing remote agents, verify that `AGENT_DESCRIPTION_JSON_DOMAIN` resolves to the deployed `ad.json`, and avoid embedding environment-specific URLs directly in source files.

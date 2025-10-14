# ANP Agent Example

[中文版本](README.cn.md) | English

This repository shows how to build and exercise an ANP (Agent Network Protocol) remote agent and companion clients. Documentation and implementation details live under `src/`; start there when you evaluate or extend the project.

## Overview

- **Remote agent**: A FastANP-powered server in `src/remote_agent.py` exposing echo and greeting interfaces.
- **Local clients**: `src/local_agent.py` and `src/local_agent_use_llm.py` demonstrate how to discover, authenticate against, and invoke remote agents.
- **Hosted environment**: The latest remote agent build is deployed and reachable via `https://agent-connect.ai/agents/test/ad.json`, so you can test without running local infrastructure.

## Prerequisites

- Python 3.9 or newer
- [uv](https://github.com/astral-sh/uv) for dependency resolution and execution

## Installation

```bash
git clone <repository-url>
cd anp-agent-example
uv sync
```

`uv sync` installs all runtime and development dependencies defined in `pyproject.toml` and `uv.lock`.

## Environment Configuration

1. Copy `env.example` to `.env`:
   ```bash
   cp env.example .env
   ```

2. Review and adjust the configuration in `.env`:
   - `HOST`: Server listen address (default: `0.0.0.0`)
   - `PORT`: Server port (default: `8000`)
   - `AGENT_DESCRIPTION_JSON_DOMAIN`: Domain used to generate `ad.json` URLs (use `localhost:8000` for local development, or your public domain like `agent-connect.ai` for deployment)

3. **OpenAI configuration is only required when running `src/local_agent_use_llm.py`**:
   - `OPENAI_API_KEY`: OpenAI API key (required)
   - `OPENAI_BASE_URL`: API endpoint (optional, supports compatible APIs like Moonshot)
   - `DEFAULT_OPENAI_MODEL`: Default model (optional)

## Running Locally

1. **Start the remote agent**
   ```bash
   PYTHONPATH=src uv run python src/remote_agent.py
   ```
   The agent serves JSON-RPC and documentation endpoints on `http://localhost:8000`.

2. **Exercise the clients**
   ```bash

   PYTHONPATH=src uv run python src/local_agent.py
   PYTHONPATH=src uv run python src/local_agent_use_llm.py
   ```
   The first command performs an end-to-end crawl and tool execution flow; the second validates the scripted ANPCrawler client; the third verifies the LLM-assisted client.

## Using the Hosted Agent

- **Agent description**: `https://agent-connect.ai/agents/test/ad.json`
- **Sample request**
  ```bash
  curl https://agent-connect.ai/agents/test/ad.json
  ```
- **JSON-RPC invocation**
  ```bash
  curl -X POST https://agent-connect.ai/agents/test/jsonrpc \
    -H "Content-Type: application/json" \
    -d '{
      "jsonrpc": "2.0",
      "method": "greet",
      "params": {"params": {"name": "Alice"}},
      "id": 1
    }'
  ```
  Replace `greet` with `echo` to exercise the inline echo interface. Authentication-sensitive endpoints expect the same DID credentials described below.

## Project Layout

```
anp-agent-example/
├── src/
│   ├── config.py              # Runtime configuration defaults and environment bindings
│   ├── remote_agent.py        # FastANP remote agent with echo and greet interfaces
│   ├── local_agent.py         # ANPCrawler client for scripted interactions
│   └── local_agent_use_llm.py # Example client incorporating LLM-assisted flows
├── docs/
│   ├── did_public/            # DID document and key material used during authentication
│   └── jwt_key/               # JWT signing assets for local testing
├── examples/                  # Lightweight runnable samples
├── run_example.py             # High-level orchestrator for local demonstrations
├── README.md
└── README.cn.md
```

## Documentation and DID Assets

- `docs/did_public/public-did-doc.json` is the DID document referenced by the clients and remote agent. You can obtain production-ready DID materials through [didhost.cc](https://didhost.cc) and replace the sample files before deploying to your environment.
- `docs/jwt_key/` contains sample RSA keys for JSON Web Token signing. Update these values or mount secrets in production.
- Inline comments and interface descriptions in `src/` provide the most up-to-date guidance on extending the system; review `remote_agent.py` when adding routes or updating `ad.json` fields.

## Development Workflow

- **Run tests**
  ```bash
  uv run pytest
  ```
- **Lint and format**
  ```bash
  uv run ruff check src tests
  uv run ruff format
  ```
- **Configuration overrides**: Copy `env.example` to `.env` to supply environment variables such as port, agent description domain, or key paths without modifying code.

## Troubleshooting

- **Port conflicts**: Update `PORT` in `src/config.py` (or override via environment variable) before starting the agent.
- **Authentication failures**: Ensure the DID document and key files in `docs/` match the credentials configured in `src/config.py`.
- **Connectivity issues**: Confirm the remote agent process is running locally, or test against the hosted deployment using the URLs above.

## License

[MIT License](LICENSE)

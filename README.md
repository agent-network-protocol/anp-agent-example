# ANP Agent Example

This is an example implementation of an ANP (Agent Network Protocol) compliant agent service built with FastAPI. It demonstrates how to build agents that support the ANP protocol, including agent description documents, DID-WBA authentication, and standardized API interfaces.

## Features

- **ANP Agent Description**: Returns agent metadata following ANP protocol specifications
- **DID-WBA Authentication**: Implements ANP protocol's DID-WBA authentication scheme
- **Multiple Interface Types**: Supports both OpenRPC structured interfaces and natural language interfaces
- **Static API Resources**: Serves JSON and YAML API definition files

## Quick Start

### Prerequisites

- Python 3.9+
- uv (recommended) or pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd anp-agent-example
```

2. Install dependencies using uv:
```bash
uv sync
```

### Running the Service

1. Configure environment variables (optional):
```bash
# Create .env file from template
cp env.example .env

# Edit .env file with your configuration
# The .env file will be automatically loaded
```

2. Start the development server:
```bash
# Recommended: Use the start script
uv run python start_anp_agent.py

# Alternative methods:
PYTHONPATH=src uv run python src/main.py
uvicorn src.main:app --reload
```

The service will be available at `http://localhost:8000`.

## API Endpoints

- `GET /` - Root endpoint with service information
- `GET /health` - Health check endpoint
- `GET /agents/test/ad.json` - Agent description (requires authentication)
- `GET /agents/test/api/{json_file}` - JSON API definition files
- `GET /agents/test/api_files/{yaml_file}` - YAML API definition files
- `GET /docs` - Interactive API documentation (Swagger UI)

## Authentication

Most endpoints require DID-WBA authentication. Include the authentication header:

```
Authorization: Bearer <your-token>
```

The following paths are exempt from authentication:
- `/`, `/health`, `/v1/status`
- `/docs`, `/redoc`, `/openapi.json`
- `/wba/user/*`

## Development

### Code Style

This project follows the Google Python Style Guide. Run linting:

```bash
uv run ruff check src tests
```

### Testing

Run tests with:

```bash
uv run pytest
```

## Documentation

For detailed architecture and implementation details, see [sepc.md](sepc.md).

## License

[MIT License](LICENSE)

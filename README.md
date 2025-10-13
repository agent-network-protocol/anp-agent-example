# ANP Agent Example

[中文版本](README.cn.md) | English

A minimal example demonstrating ANP (Agent Network Protocol) implementation using FastANP and ANPCrawler.

## Overview

This example includes:
- **Remote Agent**: A complete ANP-compliant agent (server) using FastANP
- **Local Client**: An ANPCrawler-based client that discovers and interacts with remote agents

## Quick Start

### Prerequisites

- Python 3.9+
- uv (recommended) or pip

### Installation

```bash
git clone <repository-url>
cd anp-agent-example
uv sync
```

### Running the Example

#### Step 1: Start Remote Agent

```bash
PYTHONPATH=src uv run python src/remote_agent.py
```

The remote agent will start on `http://localhost:8000`

#### Step 2: Run Client Test

In another terminal:

```bash
uv run python run_example.py
```

Or run the client directly:

```bash
PYTHONPATH=src uv run python src/local_agent.py
```

## Architecture

### Remote Agent (`src/remote_agent.py`)

A complete ANP agent built with **FastANP**:
- **ad.json**: Agent Description Document
- **echo interface** (inline in ad.json): Simple message echo
- **greet interface** (link reference): Personalized greeting with session management

**Key Endpoints:**
- `/agents/test/ad.json` - Agent Description
- `/agents/test/jsonrpc` - JSON-RPC API
- `/agents/test/api/greet.json` - Greet interface definition
- `/docs` - Swagger UI

### Local Client (`src/local_agent.py`)

An **ANPCrawler**-based client that:
- Discovers remote agents via their ad.json
- Parses interface definitions automatically
- Calls remote methods via JSON-RPC
- Manages authentication and caching

**Key Features:**
- Automatic interface discovery
- Built-in authentication (DID-WBA)
- Response caching
- Session management

## Interface Types Demo

The remote agent demonstrates two ways to include interfaces in ad.json:

### 1. Inline Interface (echo)

```python
# Full definition embedded in ad.json
if echo in anp.interfaces:
    interfaces.append(anp.interfaces[echo].content)
```

### 2. Link Reference (greet)

```python
# Link to separate file
if greet in anp.interfaces:
    interfaces.append(anp.interfaces[greet].link_summary)
```

Access the separate file at: `/agents/test/api/greet.json`

## Usage Examples

### Using ANPCrawler (Python)

```python
from local_agent import RemoteAgentClient

async def main():
    client = RemoteAgentClient("http://localhost:8000")
    
    # Discover agent
    await client.fetch_agent_description()
    
    # List available tools
    tools = await client.list_available_tools()
    
    # Test echo
    result = await client.test_echo("Hello!")
    print(result['result']['response'])
    
    # Test greet
    result = await client.test_greet("Alice")
    print(result['result']['message'])

asyncio.run(main())
```

### Using curl (Direct JSON-RPC)

**Test echo method:**
```bash
curl -X POST http://localhost:8000/agents/test/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "echo",
    "params": {"params": {"message": "Hello"}},
    "id": 1
  }'
```

**Test greet method:**
```bash
curl -X POST http://localhost:8000/agents/test/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "greet",
    "params": {"params": {"name": "Alice"}},
    "id": 1
  }'
```

**Get agent description:**
```bash
curl http://localhost:8000/agents/test/ad.json
```

**Get greet interface definition:**
```bash
curl http://localhost:8000/agents/test/api/greet.json
```

## Project Structure

```
anp-agent-example/
├── src/
│   ├── remote_agent.py    # ANP agent (FastANP)
│   ├── local_agent.py     # Client (ANPCrawler)
│   └── config.py          # Configuration
├── examples/
│   └── simple_agent_test.py
├── run_example.py         # Main test script
└── README.md
```

## Key Features

### Remote Agent (FastANP)

1. **Easy Interface Definition**: Use decorators to define interfaces
2. **Two Interface Types**: 
   - Inline (echo) - Full definition in ad.json
   - Link reference (greet) - Separate file
3. **Session Management**: Built-in session context
4. **Auto-generated OpenRPC**: Interface definitions auto-generated

### Local Client (ANPCrawler)

1. **Automatic Discovery**: Crawls and parses agent descriptions
2. **Interface Parsing**: Extracts and validates interface definitions
3. **Authentication**: Built-in DID-WBA authentication
4. **Caching**: Response caching for efficiency
5. **Session Tracking**: Tracks visited URLs and statistics

### Session Management Example

The greet method demonstrates session context usage:

```python
@anp.interface("/agents/test/api/greet.json", description="...")
def greet(params: GreetParams, ctx: Context) -> dict:
    # Access session
    session_id = ctx.session.id
    visit_count = ctx.session.get("visit_count", 0)
    visit_count += 1
    ctx.session.set("visit_count", visit_count)
    
    return {
        "message": f"Hello, {params.name}!",
        "session_id": session_id,
        "visit_count": visit_count
    }
```

## Configuration

Edit `src/config.py` or create `.env` file:

```bash
cp env.example .env
```

Key settings:
- `PORT`: Remote agent port (default: 8000)
- `AGENT_DESCRIPTION_JSON_DOMAIN`: Agent domain
- `JWT_PRIVATE_KEY_PATH`: Path to JWT private key
- `JWT_PUBLIC_KEY_PATH`: Path to JWT public key

## Development

### Run Tests

```bash
uv run pytest
```

### Code Style

```bash
uv run ruff check src
```

## API Documentation

View interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Port already in use

Change `PORT` in `src/config.py`

### Connection refused

Make sure the remote agent is running before starting the client

### Authentication errors

The client needs valid DID document and private key files:
- `docs/did_public/public-did-doc.json`
- `docs/jwt_key/RS256-private.pem`

## License

[MIT License](LICENSE)

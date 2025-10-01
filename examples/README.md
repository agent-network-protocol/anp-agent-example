# ANP Agent Client Examples

This directory contains example scripts demonstrating how to connect to and interact with the ANP agent service.

## Examples

### 1. Simple Test (`simple_test.py`)

A minimal connectivity test that verifies the agent service is running and accessible.

```bash
# Start the agent service first
cd /Users/cs/work/anp-agent-example
uv run python start_anp_agent.py

# In another terminal, run the test
uv run python examples/simple_test.py
```

**What it tests:**
- ✅ Service info endpoint (`/`)
- ✅ Health check endpoint (`/health`)
- ✅ Authentication requirement for agent description
- ✅ Mock token authentication
- ✅ API documentation availability

### 2. Full Client Example (`client_example.py`)

A comprehensive example showing how to use the ANP agent client with proper DID-WBA authentication.

### 3. DID Public Example (`did_public_example.py`)

Demonstrates real DID-WBA authentication using the DID documents from `docs/did_public/`.

```bash
# Start the server
uv run python start_anp_agent.py

# Run the DID example
uv run python examples/did_public_example.py
```

### 4. Quick Test (`quick_test.py`)

A minimal test script for quick verification.

```bash
uv run python examples/quick_test.py
```

```bash
# Install dependencies
uv sync

# Run the example
uv run python examples/client_example.py
```

**Features:**
- 🔐 DID-WBA authentication support
- 📋 Service information retrieval
- 🤖 Agent description fetching
- 🏥 Health status monitoring
- 🛡️ Proper error handling

## Usage Patterns

### Basic Connection (No Auth)

```python
import httpx

async with httpx.AsyncClient() as client:
    # Get service info
    response = await client.get("http://localhost:8000/")
    service_info = response.json()
    print(f"Service: {service_info['service']}")
```

### With Mock Authentication

```python
import httpx

async with httpx.AsyncClient() as client:
    headers = {"Authorization": "Bearer mock-token"}
    response = await client.get(
        "http://localhost:8000/agents/travel/test/ad.json",
        headers=headers
    )
    agent_desc = response.json()
    print(f"Agent: {agent_desc['name']}")
```

### With Real DID-WBA Authentication

```python
from agent_connect.authentication import DIDWbaAuthHeader
import httpx

# Setup authenticator
authenticator = DIDWbaAuthHeader(
    did_document_path="path/to/did-document.json",
    private_key_path="path/to/private-key.pem",
)

async with httpx.AsyncClient() as client:
    url = "http://localhost:8000/agents/travel/test/ad.json"
    
    # Get authentication headers
    auth_headers = authenticator.get_auth_header(url, force_new=True)
    
    # Make authenticated request
    response = await client.get(url, headers=auth_headers)
    agent_desc = response.json()
```

## Expected Responses

### Service Info Response

```json
{
  "service": "ANP智能体示例服务",
  "version": "1.0.0",
  "protocol": "ANP",
  "protocol_version": "1.0.0",
  "description": "基于FastAPI实现的ANP协议智能体示例服务",
  "endpoints": {
    "agent_description": "/agents/travel/test/ad.json",
    "api_resources": "/agents/travel/test/api/{json_file}",
    "yaml_resources": "/agents/travel/test/api_files/{yaml_file}",
    "documentation": "/docs",
    "openapi_spec": "/openapi.json"
  },
  "authentication": "DID-WBA",
  "status": "online"
}
```

### Agent Description Response

```json
{
  "protocolType": "ANP",
  "protocolVersion": "1.0.0",
  "type": "AgentDescription",
  "url": "https://agent-connect.ai/agents/travel/test/ad.json",
  "name": "测试智能体",
  "did": "did:wba:agent-connect.ai:service:test-agent",
  "owner": {
    "type": "Organization",
    "name": "agent-connect.ai",
    "url": "https://agent-connect.ai"
  },
  "description": "测试智能体，用于演示ANP协议规范的实现，提供基础的测试服务和接口示例。",
  "created": "2025-01-01T00:00:00.000Z",
  "securityDefinitions": {
    "didwba_sc": {
      "scheme": "didwba",
      "in": "header",
      "name": "Authorization"
    }
  },
  "security": "didwba_sc",
  "Infomations": [...],
  "interfaces": [...]
}
```

## Troubleshooting

### Connection Refused
```
❌ Connection error: [Errno 61] Connection refused
```
**Solution:** Make sure the ANP agent service is running:
```bash
uv run python start_anp_agent.py
```

### Authentication Required
```
❌ Failed with status: 401
```
**Solution:** This is expected for protected endpoints. Use proper DID-WBA authentication or mock tokens for testing.

### Import Errors
```
❌ ModuleNotFoundError: No module named 'agent_connect'
```
**Solution:** Install dependencies:
```bash
uv sync
```

## Next Steps

1. **Setup Real Authentication:** Create DID documents and private keys for production use
2. **Explore Interfaces:** Use the agent description to discover available interfaces
3. **Call Agent Methods:** Implement calls to the agent's OpenRPC methods
4. **Handle Errors:** Add robust error handling for production applications

For more information, see the main project documentation in `../sepc.md`.

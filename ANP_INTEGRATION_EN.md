# ANP Integration Technical Documentation

## Table of Contents

- [Overview](#overview)
- [Step 1: DID Identity Management](#step-1-did-identity-management)
  - [DID-WBA Specification](#did-wba-specification)
  - [Self-hosted DID Server](#self-hosted-did-server)
  - [Using Hosted Service](#using-hosted-service)
- [Step 2: Building ANP Agent Service](#step-2-building-anp-agent-service)
  - [FastANP Framework](#fastanp-framework)
  - [Implementation Steps](#implementation-steps)
  - [Code Examples](#code-examples)
  - [Deployment and Testing](#deployment-and-testing)
- [Step 3: Local Access to ANP Agent](#step-3-local-access-to-anp-agent)
  - [ANPCrawler Client](#anpcrawler-client)
  - [LLM-driven Agent Orchestration](#llm-driven-agent-orchestration)
  - [Implementation Steps](#implementation-steps-1)
  - [Code Examples](#code-examples-1)
- [Complete Workflow Example](#complete-workflow-example)
- [Troubleshooting and Best Practices](#troubleshooting-and-best-practices)
- [Reference Resources](#reference-resources)

---

## Overview

ANP (Agent Network Protocol) is an open protocol for agent-to-agent communication. To integrate into the ANP network, agents need to complete three core steps:

1. **Identity Management**: Establish decentralized identity through DID-WBA (Decentralized Identifier Web-Based Authentication)
2. **Service Building**: Create agent services using the FastANP framework, exposing interfaces and capabilities
3. **Client Access**: Interact with agents through ANPCrawler or LLM-driven clients

This documentation provides detailed implementation methods for these three steps, including complete code examples and best practices.

---

## Step 1: DID Identity Management

### DID-WBA Specification

DID (Decentralized Identifier) is a decentralized identity identifier that provides unique digital identities for agents. DID-WBA is a Web-based DID implementation with the following advantages:

- **Decentralized**: No dependency on central authorities
- **Verifiable**: Cryptographic methods verify identity authenticity
- **Interoperable**: Compliant with W3C DID standards
- **Web-friendly**: DID resolution through HTTP protocol

Reference specification: [DID-WBA Method Specification](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/chinese/03-did-wba%E6%96%B9%E6%B3%95%E8%A7%84%E8%8C%83.md)

### Self-hosted DID Server

If you want complete control over DID services, you can implement your own DID server by referencing `src/did_server.py`.

**Core Components:**

1. **DIDKeyManager**: Manages DID document creation and key storage
2. **DIDServer**: Provides HTTP API for DID resolution

**Implementation Steps:**

#### 1. Create DID Document and Key Pairs

```python
# examples/create_did_document.py
from anp.authentication import create_did_wba_document
import json
from pathlib import Path

def create_did_document():
    """Create a DID document and persist the generated artifacts."""
    hostname = "demo.agent-network"
    did_document, keys = create_did_wba_document(
        hostname=hostname,
        path_segments=["agents", "demo"],
        agent_description_url="https://demo.agent-network/agents/demo",
    )
    
    # Save DID document
    output_dir = Path("generated")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    did_path = output_dir / "did.json"
    did_path.write_text(json.dumps(did_document, indent=2), encoding="utf-8")
    
    # Save keys
    for fragment, (private_bytes, public_bytes) in keys.items():
        private_path = output_dir / f"{fragment}_private.pem"
        public_path = output_dir / f"{fragment}_public.pem"
        private_path.write_bytes(private_bytes)
        public_path.write_bytes(public_bytes)
    
    return did_document, keys
```

#### 2. Secure Key Storage

```python
# src/did_server.py - DIDKeyManager class
class DIDKeyManager:
    def _save_keys(self, keys: dict[str, tuple[bytes, bytes]]) -> None:
        """Save cryptographic keys to appropriate directories."""
        for fragment, (private_bytes, public_bytes) in keys.items():
            # Save private key to secure directory
            # WARNING: In production, ensure /etc/appname/keys has proper permissions:
            # - chmod 700 /etc/appname/keys
            # - chown root:root /etc/appname/keys
            private_path = Path(self.config.private_key_dir) / f"{fragment}_private.pem"
            private_path.write_bytes(private_bytes)
            # Set restrictive permissions on private key file
            os.chmod(private_path, 0o600)  # rw-------
            
            # Save public key to accessible directory
            public_path = Path(self.config.public_key_dir) / f"{fragment}_public.pem"
            public_path.write_bytes(public_bytes)
```

**Production Security Recommendations:**
- Store private keys in `/etc/appname/keys/` directory
- Set directory permissions to `700` (owner access only)
- Set private key file permissions to `600` (owner read/write only)

#### 3. Implement HTTP API Endpoints

```python
# src/did_server.py - DIDServer class
class DIDServer:
    def _register_routes(self) -> None:
        @self.app.get("/{path:path}/did.json")
        async def resolve_did(path: str) -> dict[str, Any]:
            """Resolve a DID to its DID document via HTTP GET."""
            # Convert URL path to DID identifier according to DID-WBA spec
            path_segments = path.strip("/").split("/")
            did_identifier = f"did:wba:{self.key_manager.config.hostname}:{':'.join(path_segments)}"
            
            try:
                did_document = self.key_manager.get_did_document(did_identifier)
                return did_document
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"DID document not found: {did_identifier}")
```

#### 4. URL to DID Conversion Rules

According to DID-WBA specification, URL path to DID identifier conversion rules:

- URL: `http://example.com/user/alice/did.json`
- DID: `did:wba:example.com:user:alice`

**Startup and Testing:**

```bash
# Start DID server
PYTHONPATH=src uv run python src/did_server.py

# Test DID resolution
curl http://localhost:8080/user/alice/did.json

# Expected DID document response
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:wba:localhost:user:alice",
  "verificationMethod": [...],
  "authentication": [...]
}
```

### Using Hosted Service

If you prefer not to build your own DID server, you can use the hosted service provided by [didhost.cc](https://didhost.cc/).

**didhost.cc Service Features:**

- **Cloud Creation**: Create DID documents through web interface or API
- **Key Management**: Automatically generate public/private key pairs
- **HTTP API**: Provide standard DID resolution endpoints
- **Security Guarantee**: Private keys are not stored on the server, ensuring security
- **High Availability**: Professional infrastructure and 24/7 technical support

**Quick Integration Steps:**

1. Visit [didhost.cc](https://didhost.cc/)
2. Register account and create DID document
3. Download DID document and private key files
4. Configure in your agent application

**API Example:**

```bash
# Get DID document
curl https://didhost.cc/your-did-path/did.json

# Response example
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:wba:didhost.cc:your-path",
  "verificationMethod": [...],
  "authentication": [...]
}
```

---

## Step 2: Building ANP Agent Service

### FastANP Framework

FastANP is an ANP protocol implementation framework based on FastAPI, providing a complete solution for building agent services.

**Core Concepts:**

- **Agent Description (ad.json)**: Agent description document containing basic information, interfaces, and capabilities
- **Interface**: Functional interfaces provided by agents, called via JSON-RPC
- **JSON-RPC**: JSON-based Remote Procedure Call protocol
- **Context**: Request context containing session information and DID identity
- **Session**: Session management supporting state persistence

### Implementation Steps

#### 1. Environment Configuration

First, create a `.env` file to configure environment variables:

```bash
# .env
HOST=0.0.0.0
PORT=8000
AGENT_DESCRIPTION_JSON_DOMAIN=localhost:8000
```

#### 2. Initialize FastANP Application

```python
# src/remote_agent.py
from anp.fastanp import Context, FastANP
from anp.authentication.did_wba_verifier import DidWbaVerifierConfig
from fastapi import FastAPI
from config import load_public_did, server_settings

# Initialize FastAPI app
app = FastAPI(
    title="ANP Remote Agent",
    description="Remote ANP protocol agent providing test interfaces and services",
)

# Load JWT keys for authentication
with open(JWT_PRIVATE_KEY_PATH, encoding="utf-8") as handle:
    jwt_private_key = handle.read()
with open(JWT_PUBLIC_KEY_PATH, encoding="utf-8") as handle:
    jwt_public_key = handle.read()

# Create auth config
auth_config = DidWbaVerifierConfig(
    jwt_private_key=jwt_private_key,
    jwt_public_key=jwt_public_key,
    jwt_algorithm="RS256",
    allowed_domains=["localhost", "0.0.0.0", "127.0.0.1", server_settings.agent_description_json_domain]
)

# Initialize FastANP plugin
anp = FastANP(
    app=app,
    name="Remote Test Agent",
    description="Remote ANP agent for testing agent-to-agent communication",
    agent_domain=server_settings.agent_description_json_domain,
    did=load_public_did(PUBLIC_DID_DOCUMENT_PATH),
    owner={
        "type": "Organization",
        "name": server_settings.agent_description_json_domain,
        "url": server_settings.get_agent_url(""),
    },
    jsonrpc_server_path="/agents/test/jsonrpc",
    jsonrpc_server_name="Remote Agent JSON-RPC API",
    jsonrpc_server_description="Remote Agent JSON-RPC API for ANP protocol",
    enable_auth_middleware=True,
    auth_config=auth_config
)
```

#### 3. Create ad.json Endpoint

```python
# src/remote_agent.py
@app.get("/agents/test/ad.json", tags=["agent"])
def get_agent_description():
    """Get Agent Description for the remote agent."""
    # 1. Get common header from FastANP
    ad = anp.get_common_header(agent_description_path="/agents/test/ad.json")

    # 2. Add Information items (user-defined)
    ad["information"] = [
        {
            "type": "Information",
            "description": "Remote ANP agent for testing agent-to-agent communication",
            "url": server_settings.get_agent_url("/agents/test/info/basic-info.json")
        }
    ]

    # 3. Add Interface items using FastANP helpers
    ad["interfaces"] = [
        anp.interfaces[echo].content,
        anp.interfaces[greet].content,
    ]

    return ad
```

#### 4. Register Interface Methods

```python
# src/remote_agent.py
from pydantic import BaseModel

class EchoParams(BaseModel):
    """Echo method parameters."""
    message: str

class GreetParams(BaseModel):
    """Greet method parameters."""
    name: str

# Register interface methods
@anp.interface("/agents/test/api/echo.json")
def echo(params: EchoParams) -> dict:
    """Echo a provided message."""
    return {
        "originalMessage": params.message,
        "response": f"Echo from remote: {params.message}",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

@anp.interface("/agents/test/api/greet.json")
def greet(params: GreetParams, ctx: Context) -> dict:
    """Generate personalized greeting with session context."""
    # Access session data
    session_id = ctx.session.id
    did = ctx.did

    # Store/retrieve session data
    visit_count = ctx.session.get("visit_count", 0)
    visit_count += 1
    ctx.session.set("visit_count", visit_count)

    message = f"Hello, {params.name}! Welcome to Remote ANP Agent!"

    return {
        "message": message,
        "session_id": session_id,
        "did": did,
        "visit_count": visit_count,
        "agent": "remote"
    }
```

#### 5. Context Injection (Context and Session)

FastANP automatically injects the `Context` object containing:

- `ctx.session`: Session management
- `ctx.did`: Requester's DID identifier
- `ctx.request`: Original request information

### Deployment and Testing

**Local Startup Commands:**

```bash
# Start remote agent
PYTHONPATH=src uv run python src/remote_agent.py
```

**API Documentation Access:**

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**curl Testing Examples:**

```bash
# Get agent description
curl http://localhost:8000/agents/test/ad.json

# Call echo interface
curl -X POST http://localhost:8000/agents/test/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "echo",
    "params": {"params": {"message": "Hello ANP!"}},
    "id": 1
  }'

# Call greet interface
curl -X POST http://localhost:8000/agents/test/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "greet",
    "params": {"params": {"name": "Alice"}},
    "id": 2
  }'
```

---

## Step 3: Local Access to ANP Agent

### ANPCrawler Client

ANPCrawler is a client implementation of the ANP protocol, providing complete functionality for discovering and calling remote agents.

**Main Features:**

- **Agent Discovery**: Get agent descriptions through URLs
- **Interface Discovery**: Automatically parse available tools and interfaces
- **Authentication Management**: DID-based identity verification
- **Tool Invocation**: Execute remote interface methods
- **Caching Mechanism**: Improve performance and reduce network requests

### LLM-driven Agent Orchestration

LLM-driven agent orchestration combines large language models with ANPCrawler to achieve intelligent remote agent invocation.

**Core Advantages:**

- **Natural Language Interaction**: Users can describe requirements in natural language
- **Intelligent Tool Selection**: LLM automatically selects appropriate tools
- **Dynamic Parameter Construction**: Generate correct parameters based on interface specifications
- **Multi-turn Conversation**: Support complex multi-step interaction flows

### Implementation Steps

#### 1. Initialize ANPCrawler

```python
# src/local_agent_use_llm.py
from anp.anp_crawler.anp_crawler import ANPCrawler
from pathlib import Path

class LLMLocalAgent:
    def __init__(self, agent_description_url: str):
        self.agent_description_url = agent_description_url
        
        # Paths to DID document and private key
        did_path = project_root / "docs" / "did_public" / "public-did-doc.json"
        key_path = project_root / "docs" / "did_public" / "public-private-key.pem"
        
        # Initialize ANPCrawler
        self.crawler = ANPCrawler(
            did_document_path=str(did_path),
            private_key_path=str(key_path),
            cache_enabled=True
        )
```

#### 2. Configure DID Authentication

ANPCrawler uses DID documents and private keys for identity authentication:

```python
# ANPCrawler automatically handles DID authentication
# Ensure DID document and private key files exist and are correctly formatted
did_document_path = "docs/did_public/public-did-doc.json"
private_key_path = "docs/did_public/public-private-key.pem"
```

#### 3. Get Agent Description

```python
async def fetch_agent_description(self):
    """Fetch and display the remote agent description."""
    try:
        # Use fetch_text method to get agent description
        content_json, interfaces_list = await self.crawler.fetch_text(self.agent_description_url)
        
        # Parse and display JSON content
        parsed_content = json.loads(content_json["content"])
        logger.info(f"Name: {parsed_content.get('name')}")
        logger.info(f"DID: {parsed_content.get('did')}")
        logger.info(f"Interfaces found: {len(interfaces_list)}")
        
        return content_json, interfaces_list
    except Exception as e:
        logger.error(f"Failed to fetch agent description: {str(e)}")
        raise
```

#### 4. Discover Available Tools

```python
async def list_available_tools(self):
    """List all available tools discovered by the crawler."""
    tools = self.crawler.list_available_tools()
    
    for tool_name in tools:
        tool_info = self.crawler.get_tool_interface_info(tool_name)
        logger.info(f"Tool: {tool_name}")
        logger.info(f"Method: {tool_info.get('method_name', 'N/A')}")
    
    return tools
```

#### 5. Execute Remote Calls

```python
async def call_tool(self, tool_name: str, arguments: dict):
    """Call a remote tool using ANPCrawler."""
    try:
        result = await self.crawler.execute_tool_call(tool_name, arguments)
        logger.info(f"Tool call result: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        logger.error(f"Tool call failed: {str(e)}")
        raise
```

#### 6. LLM Integration

```python
# src/local_agent_use_llm.py
from openai import OpenAI

class LLMLocalAgent:
    def __init__(self, agent_description_url: str, model: str = "gpt-4o-mini"):
        # ... ANPCrawler initialization ...
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=openai_settings.api_key)
        self.tools = self._build_tool_definitions()
        self.system_prompt = self._build_system_prompt()
    
    def _build_tool_definitions(self) -> list[dict[str, Any]]:
        """Expose ANPCrawler capabilities to the model."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "fetch_text",
                    "description": "Fetch structured documents through ANPCrawler",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": f"Absolute URL to fetch using ANPCrawler"
                            }
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_tool_call",
                    "description": "Execute a remote interface discovered via ANPCrawler",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tool_name": {
                                "type": "string",
                                "description": "Name of the interface method to execute"
                            },
                            "arguments": {
                                "type": "object",
                                "description": "JSON payload to send to the remote method"
                            }
                        },
                        "required": ["tool_name", "arguments"],
                    },
                },
            },
        ]
    
    async def run(self, prompt: str) -> str:
        """Drive a tool-augmented conversation with the LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        
        while True:
            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=0.0,
                tools=self.tools,
                tool_choice="auto",
            )
            
            choice = completion.choices[0]
            message = choice.message
            
            # Add assistant message
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ] if message.tool_calls else None
            })
            
            if not message.tool_calls:
                return message.content or ""
            
            # Execute tool calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                
                tool_result = await self._invoke_tool(tool_name, args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
    
    async def _invoke_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatch tool invocations to the appropriate ANPCrawler method."""
        if tool_name == "fetch_text":
            return await self._handle_fetch_text(args)
        if tool_name == "execute_tool_call":
            return await self._handle_execute_tool_call(args)
        return {"error": f"Unknown tool: {tool_name}"}
    
    async def _handle_fetch_text(self, args: dict[str, Any]) -> dict[str, Any]:
        """Wrap ANPCrawler.fetch_text for LLM consumption."""
        url = args.get("url")
        if not isinstance(url, str):
            return {"error": "fetch_text requires a string 'url' field."}
        
        try:
            content_json, interfaces = await self.crawler.fetch_text(url)
            return {
                "content": content_json,
                "interfaces": interfaces,
            }
        except Exception as exc:
            return {"error": f"fetch_text failed: {exc}"}
    
    async def _handle_execute_tool_call(self, args: dict[str, Any]) -> dict[str, Any]:
        """Wrap ANPCrawler.execute_tool_call for LLM consumption."""
        tool = args.get("tool_name")
        payload = args.get("arguments", {})
        
        if not isinstance(tool, str):
            return {"error": "execute_tool_call requires 'tool_name' as string."}
        
        try:
            result = await self.crawler.execute_tool_call(tool, payload)
            return {"result": result}
        except Exception as exc:
            return {"error": f"execute_tool_call failed: {exc}"}
```

### Running Examples

**Environment Variable Configuration:**

```bash
# .env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_OPENAI_MODEL=gpt-4o-mini
HOST=0.0.0.0
PORT=8000
AGENT_DESCRIPTION_JSON_DOMAIN=localhost:8000
```

**Startup Commands:**

```bash
# Start remote agent
PYTHONPATH=src uv run python src/remote_agent.py

# Run LLM client
PYTHONPATH=src uv run python src/local_agent_use_llm.py
```

**Expected Output:**

```
2024-01-15 10:30:00 - INFO - Starting LLM agent with prompt: Please use the echo tool to send the message 'Hello from LLM Agent!' and show me the response.
2024-01-15 10:30:01 - INFO - LLM requested 1 tool call(s)
2024-01-15 10:30:01 - INFO - Calling tool: fetch_text
2024-01-15 10:30:02 - INFO - Tool result: {"content": {...}, "interfaces": [...]}
2024-01-15 10:30:03 - INFO - LLM requested 1 tool call(s)
2024-01-15 10:30:03 - INFO - Calling tool: execute_tool_call
2024-01-15 10:30:04 - INFO - Tool result: {"result": {"originalMessage": "Hello from LLM Agent!", "response": "Echo from remote: Hello from LLM Agent!", "timestamp": "2024-01-15T10:30:04Z"}}
2024-01-15 10:30:05 - INFO - Final Response: I successfully used the echo tool to send your message. Here's the response: "Echo from remote: Hello from LLM Agent!"
```

---

## Complete Workflow Example

**End-to-End Scenario Demonstration:**

1. **DID Identity Creation**
   - Use `examples/create_did_document.py` to create DID document
   - Generate public/private key pairs
   - Configure in agent application

2. **Agent Service Building**
   - Initialize agent using FastANP
   - Register interface methods (echo, greet)
   - Start service and expose ad.json

3. **Client Access**
   - ANPCrawler discovers agent
   - LLM understands user requirements
   - Automatically calls appropriate interfaces
   - Returns results to user

**Complete Workflow Diagram (Text Description):**

```
User inputs natural language requirements
    ↓
LLM parses requirements and selects tools
    ↓
ANPCrawler gets agent description
    ↓
Discover available interfaces (echo, greet)
    ↓
LLM constructs parameters and calls interface
    ↓
Remote agent processes request
    ↓
Returns results to LLM
    ↓
LLM formats results and replies to user
```

---

## Troubleshooting and Best Practices

### Common Issues and Solutions

**1. DID Authentication Failure**
- Check if DID document format is correct
- Confirm private key file exists and has correct permissions
- Verify DID resolution URL is accessible

**2. Agent Service Startup Failure**
- Check if port is occupied
- Confirm environment variables are configured correctly
- Verify JWT key files exist

**3. LLM Client Connection Failure**
- Confirm OpenAI API key is valid
- Check network connectivity
- Verify model name is correct

### Production Deployment Recommendations

**1. Security Configuration**
- Use HTTPS protocol
- Set appropriate CORS policies
- Regularly rotate JWT keys

**2. Performance Optimization**
- Enable ANPCrawler caching
- Use connection pooling
- Monitor service performance

**3. Monitoring and Logging**
- Configure structured logging
- Set up health check endpoints
- Monitor key metrics

---

## Reference Resources

- **ANP Protocol Specification**: [Agent Network Protocol](https://github.com/agent-network-protocol/AgentNetworkProtocol)
- **DID-WBA Method Specification**: [DID-WBA Method Specification](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/chinese/03-did-wba%E6%96%B9%E6%B3%95%E8%A7%84%E8%8C%83.md)
- **FastANP Framework**: ANP implementation based on FastAPI
- **ANPCrawler Client**: ANP protocol client implementation

**Related File Index:**
- `src/did_server.py` - DID server implementation
- `src/remote_agent.py` - Remote agent implementation
- `src/local_agent_use_llm.py` - LLM client implementation
- `examples/create_did_document.py` - DID document creation example
- `docs/did_public/public-did-doc.json` - Example DID document

**External Resources:**
- [didhost.cc](https://didhost.cc/) - DID hosting service
- [OpenAI API](https://platform.openai.com/) - LLM service
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework

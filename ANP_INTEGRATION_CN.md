# ANP 接入技术文档

## 目录

- [概览](#概览)
- [第一步：DID 身份管理](#第一步did-身份管理)
  - [DID-WBA 规范简介](#did-wba-规范简介)
  - [自建 DID 服务器](#自建-did-服务器)
  - [使用托管服务](#使用托管服务)
- [第二步：搭建 ANP 智能体服务](#第二步搭建-anp-智能体服务)
  - [FastANP 框架介绍](#fastanp-框架介绍)
  - [实现步骤](#实现步骤)
  - [代码示例](#代码示例)
  - [部署和测试](#部署和测试)
- [第三步：本地访问 ANP 智能体](#第三步本地访问-anp-智能体)
  - [ANPCrawler 客户端](#anpcrawler-客户端)
  - [LLM 驱动的智能体编排](#llm-驱动的智能体编排)
  - [实现步骤](#实现步骤-1)
  - [代码示例](#代码示例-1)
- [完整工作流程示例](#完整工作流程示例)
- [故障排查和最佳实践](#故障排查和最佳实践)
- [参考资源](#参考资源)

---

## 概览

ANP（Agent Network Protocol）是一个用于智能体间通信的开放协议。要接入 ANP 网络，智能体需要完成三个核心步骤：

1. **身份管理**：通过 DID-WBA（Decentralized Identifier Web-Based Authentication）建立去中心化身份
2. **服务搭建**：使用 FastANP 框架创建智能体服务，暴露接口和功能
3. **客户端访问**：通过 ANPCrawler 或 LLM 驱动的客户端与智能体交互

本文档将详细介绍这三个步骤的实现方法，包含完整的代码示例和最佳实践。

---

## 第一步：DID 身份管理

### DID-WBA 规范简介

DID（Decentralized Identifier）是一种去中心化身份标识符，为智能体提供独特的数字身份。DID-WBA 是基于 Web 的 DID 实现方案，具有以下优势：

- **去中心化**：不依赖中央权威机构
- **可验证性**：通过密码学方法验证身份真实性
- **互操作性**：符合 W3C DID 标准
- **Web 友好**：通过 HTTP 协议进行 DID 解析

参考规范：[DID-WBA 方法规范](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/chinese/03-did-wba%E6%96%B9%E6%B3%95%E8%A7%84%E8%8C%83.md)

### 自建 DID 服务器

如果您希望完全控制 DID 服务，可以参考 `src/did_server.py` 实现自己的 DID 服务器。

**核心组件：**

1. **DIDKeyManager**：管理 DID 文档创建和密钥存储
2. **DIDServer**：提供 HTTP API 进行 DID 解析

**实现步骤：**

#### 1. 创建 DID 文档和密钥对

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

#### 2. 密钥安全存储

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

**生产环境安全建议：**
- 私钥存储在 `/etc/appname/keys/` 目录
- 设置目录权限为 `700`（仅所有者可访问）
- 私钥文件权限设置为 `600`（仅所有者可读写）

#### 3. 实现 HTTP API 端点

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

#### 4. URL 到 DID 转换规则

根据 DID-WBA 规范，URL 路径转换为 DID 标识符的规则：

- URL: `http://example.com/user/alice/did.json`
- DID: `did:wba:example.com:user:alice`

**启动和测试：**

```bash
# 启动 DID 服务器
PYTHONPATH=src uv run python src/did_server.py

# 测试 DID 解析
curl http://localhost:8080/user/alice/did.json

# 预期返回 DID 文档
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:wba:localhost:user:alice",
  "verificationMethod": [...],
  "authentication": [...]
}
```

### 使用托管服务

如果您不想自己搭建 DID 服务器，可以使用 [didhost.cc](https://didhost.cc/) 提供的托管服务。

**didhost.cc 服务特点：**

- **云端创建**：通过 Web 界面或 API 创建 DID 文档
- **密钥管理**：自动生成公钥/私钥对
- **HTTP API**：提供标准的 DID 解析端点
- **安全保证**：私钥不会在服务器端保存，确保安全性
- **高可用性**：专业的基础设施和 24/7 技术支持

**快速接入步骤：**

1. 访问 [didhost.cc](https://didhost.cc/)
2. 注册账户并创建 DID 文档
3. 下载 DID 文档和私钥文件
4. 配置到您的智能体应用中

**API 示例：**

```bash
# 获取 DID 文档
curl https://didhost.cc/your-did-path/did.json

# 返回示例
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:wba:didhost.cc:your-path",
  "verificationMethod": [...],
  "authentication": [...]
}
```

---

## 第二步：搭建 ANP 智能体服务

### FastANP 框架介绍

FastANP 是基于 FastAPI 的 ANP 协议实现框架，提供了构建智能体服务的完整解决方案。

**核心概念：**

- **Agent Description (ad.json)**：智能体描述文档，包含基本信息、接口和能力
- **Interface**：智能体提供的功能接口，通过 JSON-RPC 调用
- **JSON-RPC**：基于 JSON 的远程过程调用协议
- **Context**：请求上下文，包含会话信息和 DID 身份
- **Session**：会话管理，支持状态持久化

### 实现步骤

#### 1. 环境配置

首先创建 `.env` 文件配置环境变量：

```bash
# .env
HOST=0.0.0.0
PORT=8000
AGENT_DESCRIPTION_JSON_DOMAIN=localhost:8000
```

#### 2. 初始化 FastANP 应用

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

#### 3. 创建 ad.json 端点

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

#### 4. 注册 Interface 方法

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

#### 5. 上下文注入（Context 和 Session）

FastANP 自动注入 `Context` 对象，包含：

- `ctx.session`：会话管理
- `ctx.did`：请求者的 DID 标识符
- `ctx.request`：原始请求信息

### 部署和测试

**本地启动命令：**

```bash
# 启动远程智能体
PYTHONPATH=src uv run python src/remote_agent.py
```

**API 文档访问：**

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**curl 测试示例：**

```bash
# 获取智能体描述
curl http://localhost:8000/agents/test/ad.json

# 调用 echo 接口
curl -X POST http://localhost:8000/agents/test/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "echo",
    "params": {"params": {"message": "Hello ANP!"}},
    "id": 1
  }'

# 调用 greet 接口
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

## 第三步：本地访问 ANP 智能体

### ANPCrawler 客户端

ANPCrawler 是 ANP 协议的客户端实现，提供了发现和调用远程智能体的完整功能。

**主要功能：**

- **智能体发现**：通过 URL 获取智能体描述
- **接口发现**：自动解析可用的工具和接口
- **认证管理**：基于 DID 的身份验证
- **工具调用**：执行远程接口方法
- **缓存机制**：提高性能和减少网络请求

### LLM 驱动的智能体编排

LLM 驱动的智能体编排将大语言模型与 ANPCrawler 结合，实现智能的远程智能体调用。

**核心优势：**

- **自然语言交互**：用户可以用自然语言描述需求
- **智能工具选择**：LLM 自动选择合适的工具
- **动态参数构建**：根据接口规范生成正确的参数
- **多轮对话**：支持复杂的多步骤交互流程

### 实现步骤

#### 1. 初始化 ANPCrawler

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

#### 2. 配置 DID 认证

ANPCrawler 使用 DID 文档和私钥进行身份认证：

```python
# ANPCrawler 自动处理 DID 认证
# 确保 DID 文档和私钥文件存在且格式正确
did_document_path = "docs/did_public/public-did-doc.json"
private_key_path = "docs/did_public/public-private-key.pem"
```

#### 3. 获取智能体描述

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

#### 4. 发现可用工具

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

#### 5. 执行远程调用

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

#### 6. LLM 集成

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

### 运行示例

**环境变量配置：**

```bash
# .env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_OPENAI_MODEL=gpt-4o-mini
HOST=0.0.0.0
PORT=8000
AGENT_DESCRIPTION_JSON_DOMAIN=localhost:8000
```

**启动命令：**

```bash
# 启动远程智能体
PYTHONPATH=src uv run python src/remote_agent.py

# 运行 LLM 客户端
PYTHONPATH=src uv run python src/local_agent_use_llm.py
```

**预期输出：**

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

## 完整工作流程示例

**端到端场景演示：**

1. **DID 身份创建**
   - 使用 `examples/create_did_document.py` 创建 DID 文档
   - 生成公钥/私钥对
   - 配置到智能体应用中

2. **智能体服务搭建**
   - 使用 FastANP 初始化智能体
   - 注册接口方法（echo、greet）
   - 启动服务并暴露 ad.json

3. **客户端访问**
   - ANPCrawler 发现智能体
   - LLM 理解用户需求
   - 自动调用合适的接口
   - 返回结果给用户

**完整流程图（文字描述）：**

```
用户输入自然语言需求
    ↓
LLM 解析需求并选择工具
    ↓
ANPCrawler 获取智能体描述
    ↓
发现可用接口（echo、greet）
    ↓
LLM 构建参数并调用接口
    ↓
远程智能体处理请求
    ↓
返回结果给 LLM
    ↓
LLM 格式化结果并回复用户
```

---

## 故障排查和最佳实践

### 常见问题和解决方案

**1. DID 认证失败**
- 检查 DID 文档格式是否正确
- 确认私钥文件存在且权限正确
- 验证 DID 解析 URL 是否可访问

**2. 智能体服务启动失败**
- 检查端口是否被占用
- 确认环境变量配置正确
- 验证 JWT 密钥文件存在

**3. LLM 客户端连接失败**
- 确认 OpenAI API 密钥有效
- 检查网络连接
- 验证模型名称正确

### 生产环境部署建议

**1. 安全配置**
- 使用 HTTPS 协议
- 设置适当的 CORS 策略
- 定期轮换 JWT 密钥

**2. 性能优化**
- 启用 ANPCrawler 缓存
- 使用连接池
- 监控服务性能

**3. 监控和日志**
- 配置结构化日志
- 设置健康检查端点
- 监控关键指标

---

## 参考资源

- **ANP 协议规范**：[Agent Network Protocol](https://github.com/agent-network-protocol/AgentNetworkProtocol)
- **DID-WBA 方法规范**：[DID-WBA 方法规范](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/chinese/03-did-wba%E6%96%B9%E6%B3%95%E8%A7%84%E8%8C%83.md)
- **FastANP 框架**：基于 FastAPI 的 ANP 实现
- **ANPCrawler 客户端**：ANP 协议客户端实现

**相关文件索引：**
- `src/did_server.py` - DID 服务器实现
- `src/remote_agent.py` - 远程智能体实现
- `src/local_agent_use_llm.py` - LLM 客户端实现
- `examples/create_did_document.py` - DID 文档创建示例
- `docs/did_public/public-did-doc.json` - 示例 DID 文档

**外部资源：**
- [didhost.cc](https://didhost.cc/) - DID 托管服务
- [OpenAI API](https://platform.openai.com/) - LLM 服务
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

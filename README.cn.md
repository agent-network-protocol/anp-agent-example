# ANP 智能体示例

中文版本 | [English](README.md)

一个最小化的示例，演示使用 FastANP 和 ANPCrawler 实现 ANP（智能体网络协议）。

## 概述

本示例包括：
- **远程智能体**：使用 FastANP 构建的完整 ANP 智能体（服务端）
- **本地客户端**：基于 ANPCrawler 的客户端，可以发现并与远程智能体交互

## 快速开始

### 前置要求

- Python 3.9+
- uv（推荐）或 pip

### 安装

```bash
git clone <repository-url>
cd anp-agent-example
uv sync
```

### 运行示例

#### 步骤 1：启动远程智能体

```bash
PYTHONPATH=src uv run python src/remote_agent.py
```

远程智能体将在 `http://localhost:8000` 启动

#### 步骤 2：运行客户端测试

在另一个终端：

```bash
uv run python run_example.py
```

或直接运行客户端：

```bash
PYTHONPATH=src uv run python src/local_agent.py
```

## 架构

### 远程智能体（`src/remote_agent.py`）

使用 **FastANP** 构建的完整 ANP 智能体：
- **ad.json**：智能体描述文档
- **echo 接口**（内联在 ad.json 中）：简单消息回显
- **greet 接口**（链接引用）：带会话管理的个性化问候

**关键端点：**
- `/agents/test/ad.json` - 智能体描述
- `/agents/test/jsonrpc` - JSON-RPC API
- `/agents/test/api/greet.json` - Greet 接口定义
- `/docs` - Swagger UI

### 本地客户端（`src/local_agent.py`）

基于 **ANPCrawler** 的客户端：
- 通过 ad.json 发现远程智能体
- 自动解析接口定义
- 通过 JSON-RPC 调用远程方法
- 管理认证和缓存

**关键特性：**
- 自动接口发现
- 内置认证（DID-WBA）
- 响应缓存
- 会话管理

## 接口类型演示

远程智能体演示了在 ad.json 中包含接口的两种方式：

### 1. 内联接口（echo）

```python
# 完整定义嵌入在 ad.json 中
if echo in anp.interfaces:
    interfaces.append(anp.interfaces[echo].content)
```

### 2. 链接引用（greet）

```python
# 链接到单独文件
if greet in anp.interfaces:
    interfaces.append(anp.interfaces[greet].link_summary)
```

访问单独文件：`/agents/test/api/greet.json`

## 使用示例

### 使用 ANPCrawler（Python）

```python
from local_agent import RemoteAgentClient

async def main():
    client = RemoteAgentClient("http://localhost:8000")
    
    # 发现智能体
    await client.fetch_agent_description()
    
    # 列出可用工具
    tools = await client.list_available_tools()
    
    # 测试 echo
    result = await client.test_echo("你好！")
    print(result['result']['response'])
    
    # 测试 greet
    result = await client.test_greet("Alice")
    print(result['result']['message'])

asyncio.run(main())
```

### 使用 curl（直接 JSON-RPC）

**测试 echo 方法：**
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

**测试 greet 方法：**
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

**获取智能体描述：**
```bash
curl http://localhost:8000/agents/test/ad.json
```

**获取 greet 接口定义：**
```bash
curl http://localhost:8000/agents/test/api/greet.json
```

## 项目结构

```
anp-agent-example/
├── src/
│   ├── remote_agent.py    # ANP 智能体（FastANP）
│   ├── local_agent.py     # 客户端（ANPCrawler）
│   └── config.py          # 配置
├── examples/
│   └── simple_agent_test.py
├── run_example.py         # 主测试脚本
└── README.md
```

## 主要特性

### 远程智能体（FastANP）

1. **简单的接口定义**：使用装饰器定义接口
2. **两种接口类型**：
   - 内联（echo）- 完整定义在 ad.json 中
   - 链接引用（greet）- 单独文件
3. **会话管理**：内置会话上下文
4. **自动生成 OpenRPC**：接口定义自动生成

### 本地客户端（ANPCrawler）

1. **自动发现**：爬取并解析智能体描述
2. **接口解析**：提取并验证接口定义
3. **认证**：内置 DID-WBA 认证
4. **缓存**：响应缓存提高效率
5. **会话跟踪**：跟踪访问的 URL 和统计信息

### 会话管理示例

greet 方法展示了会话上下文的使用：

```python
@anp.interface("/agents/test/api/greet.json", description="...")
def greet(params: GreetParams, ctx: Context) -> dict:
    # 访问会话
    session_id = ctx.session.id
    visit_count = ctx.session.get("visit_count", 0)
    visit_count += 1
    ctx.session.set("visit_count", visit_count)
    
    return {
        "message": f"你好, {params.name}!",
        "session_id": session_id,
        "visit_count": visit_count
    }
```

## 配置

编辑 `src/config.py` 或创建 `.env` 文件：

```bash
cp env.example .env
```

关键设置：
- `PORT`：远程智能体端口（默认：8000）
- `AGENT_DESCRIPTION_JSON_DOMAIN`：智能体域名
- `JWT_PRIVATE_KEY_PATH`：JWT 私钥路径
- `JWT_PUBLIC_KEY_PATH`：JWT 公钥路径

## 开发

### 运行测试

```bash
uv run pytest
```

### 代码风格

```bash
uv run ruff check src
```

## API 文档

查看交互式 API 文档：
- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

## 故障排除

### 端口已被占用

修改 `src/config.py` 中的 `PORT`

### 连接被拒绝

确保在启动客户端之前远程智能体已经运行

### 认证错误

客户端需要有效的 DID 文档和私钥文件：
- `docs/did_public/public-did-doc.json`
- `docs/jwt_key/RS256-private.pem`

## 许可证

[MIT License](LICENSE)

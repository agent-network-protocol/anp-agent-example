# ANP 智能体示例

中文版本 | [English](README.md)

本仓库展示如何构建并验证 ANP（Agent Network Protocol）远程智能体及配套客户端。实现细节与文档集中在 `src/` 目录，评估或扩展功能时请首先阅读该目录下的代码。

## 概览

- **远程智能体**：`src/remote_agent.py` 使用 FastANP 暴露 echo 与 greet 接口。
- **本地客户端**：`src/local_agent.py`、`src/local_agent_use_llm.py` 演示如何发现、认证并调用远程智能体。
- **托管环境**：最新版本的远程智能体已部署，可通过 `https://agent-connect.ai/agents/test/ad.json` 直接测试，无需本地启动服务端。

## 前置要求

- Python 3.9 及以上
- [uv](https://github.com/astral-sh/uv)（用于依赖解析与运行）

## 安装

```bash
git clone <repository-url>
cd anp-agent-example
uv sync
```

`uv sync` 会根据 `pyproject.toml` 与 `uv.lock` 安装运行期与开发依赖。

## 环境配置

1. 复制 `env.example` 到 `.env`：
   ```bash
   cp env.example .env
   ```

2. 按需调整 `.env` 中的配置：
   - `HOST`：服务监听地址（默认 `0.0.0.0`）
   - `PORT`：服务端口（默认 `8000`）
   - `AGENT_DESCRIPTION_JSON_DOMAIN`：用于生成 `ad.json` URL 的域名（本地调试设为 `localhost:8000`，线上部署改为公开域名如 `agent-connect.ai`）

3. **仅在运行 `src/local_agent_use_llm.py` 时需要配置 OpenAI**：
   - `OPENAI_API_KEY`：OpenAI API 密钥（必填）
   - `OPENAI_BASE_URL`：API 端点（可选，支持兼容接口如 Moonshot）
   - `DEFAULT_OPENAI_MODEL`：默认模型（可选）

## 本地运行

1. **启动远程智能体**
   ```bash
   PYTHONPATH=src uv run python src/remote_agent.py
   ```
   服务启动后会在 `http://localhost:8000` 提供 JSON-RPC 与文档端点。

2. **运行客户端脚本**
   ```bash
   uv run python run_example.py
   PYTHONPATH=src uv run python src/local_agent.py
   PYTHONPATH=src uv run python src/local_agent_use_llm.py
   ```
   第一条命令展示完整的抓取与工具调用流程；第二条验证脚本化客户端；第三条验证引入 LLM 的客户端。

## 访问托管的远端智能体

- **智能体描述**：`https://agent-connect.ai/agents/test/ad.json`
- **示例请求**
  ```bash
  curl https://agent-connect.ai/agents/test/ad.json
  ```
- **JSON-RPC 调用**
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
  将 `greet` 替换为 `echo` 即可测试内联 echo 接口。若端点需要认证，请使用下文提到的 DID 凭证。

## 项目结构

```
anp-agent-example/
├── src/
│   ├── config.py              # 运行时配置默认值与环境变量绑定
│   ├── remote_agent.py        # FastANP 远程智能体，提供 echo/greet 接口
│   ├── local_agent.py         # 基于 ANPCrawler 的脚本化客户端
│   └── local_agent_use_llm.py # 演示引入大模型辅助的客户端流程
├── docs/
│   ├── did_public/            # DID 文档与密钥示例，供认证使用
│   └── jwt_key/               # JWT 签名资产，用于本地测试
├── examples/                  # 轻量级可运行示例
├── run_example.py             # 本地演示的高层封装
├── README.md
└── README.cn.md
```

## 文档与 DID 资源

- `docs/did_public/public-did-doc.json` 是客户端与远程智能体引用的 DID 文档。生产环境可前往 [didhost.cc](https://didhost.cc) 申请正式 DID，并替换示例文件。
- `docs/jwt_key/` 内提供示例 RSA 密钥，用于 JSON Web Token 签名。部署前请更换为安全的密钥或改为读取外部机密。
- `src/` 中的内联注释与接口描述提供扩展指引，新增路由或更新 `ad.json` 字段时请优先查阅 `remote_agent.py`。

## 开发流程

- **运行测试**
  ```bash
  uv run pytest
  ```
- **代码检查与格式化**
  ```bash
  uv run ruff check src tests
  uv run ruff format
  ```
- **配置覆盖**：复制 `env.example` 为 `.env`，可在不改动代码的前提下覆写端口、域名、密钥路径等环境变量。

## 故障排查

- **端口冲突**：在 `src/config.py`（或环境变量）中调整 `PORT`。
- **认证失败**：确认 `docs/` 下的 DID 与密钥文件与 `src/config.py` 保持一致。
- **连接问题**：检查本地服务是否运行，或直接改用托管地址进行验证。

## 许可证

[MIT License](LICENSE)

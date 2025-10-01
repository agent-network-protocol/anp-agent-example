# ANP 智能体示例

中文版本 | [English](README.md)

这是一个基于 FastAPI 构建的 ANP（智能体网络协议）兼容智能体服务的示例实现。它演示了如何构建支持 ANP 协议的智能体，包括智能体描述文档、DID-WBA 认证和标准化 API 接口。

## 功能特性

- **ANP 智能体描述**：返回符合 ANP 协议规范的智能体元数据
- **DID-WBA 认证**：实现 ANP 协议的 DID-WBA 认证方案
- **多种接口类型**：支持 OpenRPC 结构化接口和自然语言接口
- **静态 API 资源**：提供 JSON 和 YAML API 定义文件服务

## 快速开始

### 前置要求

- Python 3.9+
- uv（推荐）或 pip

### 安装

1. 克隆仓库：
```bash
git clone <repository-url>
cd anp-agent-example
```

2. 使用 uv 安装依赖：
```bash
uv sync
```

### 运行服务

1. 配置环境变量（可选）：
```bash
# 从模板创建 .env 文件
cp env.example .env

# 编辑 .env 文件配置你的设置
# .env 文件将自动加载
```

2. 启动开发服务器：
```bash
# 推荐：使用启动脚本
uv run python start_anp_agent.py

# 其他方法：
PYTHONPATH=src uv run python src/main.py
uvicorn src.main:app --reload
```

服务将在 `http://localhost:8000` 上可用。

此外，该服务已部署，可通过访问 https://agent-connect.ai/agents/test/ad.json 进行测试。

## API 端点

- `GET /` - 根端点，包含服务信息
- `GET /health` - 健康检查端点
- `GET /agents/test/ad.json` - 智能体描述（需要认证）
- `GET /agents/test/api/{json_file}` - JSON API 定义文件
- `GET /agents/test/api_files/{yaml_file}` - YAML API 定义文件
- `GET /docs` - 交互式 API 文档（Swagger UI）

## 认证

大多数端点需要 DID-WBA 认证。请包含认证头：

```
Authorization: Bearer <your-token>
```

以下路径免于认证：
- `/`, `/health`, `/v1/status`
- `/docs`, `/redoc`, `/openapi.json`
- `/wba/user/*`

## 开发

### 代码风格

本项目遵循 Google Python 风格指南。运行代码检查：

```bash
uv run ruff check src tests
```

### 测试

运行测试：

```bash
uv run pytest
```

## 文档

详细的架构和实现细节，请参见 [sepc.md](sepc.md)。

## 许可证

[MIT License](LICENSE)
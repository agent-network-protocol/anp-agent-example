# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个ANP（智能体网络协议）智能体示例服务，基于FastAPI实现，展示如何构建符合ANP规范的智能体，包括智能体描述文档、DID-WBA身份验证和标准化API接口。

## 常用开发命令

### 依赖管理
- `uv sync` - 安装或刷新pyproject.toml中列出的依赖项
- `uv add <package>` - 添加新的依赖包

### 运行服务
- `python main.py` - 启动开发服务器
- `uvicorn main:app --reload` - 使用uvicorn直接启动服务
- 服务默认运行在 `http://localhost:8000`
- 需要设置环境变量：`AGENT_DESCRIPTION_JSON_DOMAIN=agent-connect.ai`

### 代码质量检查
- `uv run ruff check . tests` - 运行代码规范检查（必须在提交前通过）
- `uv run ruff format .` - 自动格式化代码
- `uv run mypy .` - 运行类型检查

### 测试
- `uv run pytest` - 运行完整测试套件
- `uv run pytest -k <expr>` - 运行匹配表达式的特定测试
- `uv run pytest --cov` - 运行测试并生成覆盖率报告

### 静态资源测试
- `uv run python -m http.server --directory api 9000` - 对api目录下的静态文件进行smoke测试

## 核心架构

### 主要模块结构
- **main.py** - 应用入口点，配置FastAPI应用、中间件和路由
- **ad_router.py** - 智能体描述路由，提供ANP规范的智能体元数据
- **api_router.py** - JSON API定义文件服务，提供OpenRPC接口文档
- **yaml_router.py** - YAML API定义文件服务
- **auth_middleware.py** - DID-WBA身份验证中间件，集成agent-connect库
- **config.py** - 配置管理和设置

### API端点结构
- `/` - 根端点，提供服务信息
- `/health` - 健康检查端点
- `/agents/test/ad.json` - 智能体描述（需要身份验证）
- `/agents/test/api/{json_file}` - JSON API定义文件
- `/agents/test/api_files/{yaml_file}` - YAML API定义文件

### 身份验证
- 使用DID-WBA身份验证方案（基于agent-connect库）
- 豁免路径：`/`, `/health`, `/v1/status`, `/docs`, `/redoc`, `/openapi.json`, `/wba/user/*`
- 需要Authentication header: `Authorization: Bearer <token>`

### 静态资源
- **api/** 目录存放JSON和YAML格式的API接口定义文件
- 这些文件被相应的路由器提供服务

## 开发规范

### 代码风格
- 遵循Google Python编程规范，使用四空格缩进
- 函数和模块使用snake_case命名，类使用PascalCase
- 必须添加类型提示和简洁的文档字符串
- 使用模块级别的`logger = logging.getLogger(__name__)`记录日志
- 保持注释和日志为英文

### 模块组织原则
- 每个路由器专注于单一协议关注点
- 通过添加辅助函数扩展auth_middleware.py，而不是在处理程序内联复杂逻辑
- 将验证辅助函数组织在私有函数中，保持请求处理程序简短和可测试

### 测试要求
- 测试文件放在`tests/`目录下，镜像被测试的包结构
- 使用pytest配合pytest-asyncio和httpx.AsyncClient测试异步端点
- 目标是≥85%的语句覆盖率，在触及的模块上
- 为修复协议文档的错误包含回归测试

## 配置和安全

### 环境变量
- `AGENT_DESCRIPTION_JSON_DOMAIN` - 智能体描述JSON域名（必需）
- 密钥路径由特定于环境的设置提供，不要提交机密信息
- 本地覆盖存储在被忽略的`.env`文件中

### API接口验证
- 合并前验证修改的JSON/YAML工件符合其架构，防止破坏依赖的智能体
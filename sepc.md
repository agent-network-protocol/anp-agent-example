# ANP智能体示例项目架构设计与实现方案

## 项目概述

本项目是一个基于FastAPI框架的ANP（Agent Network Protocol）智能体示例实现，展示了如何构建符合ANP协议规范的智能体服务。项目实现了完整的智能体描述协议、DID-WBA身份认证机制，以及标准化的API接口服务。

### 核心功能

- **智能体描述服务**：提供符合ANP规范的智能体描述文档，包含基本信息和接口描述
- **DID-WBA认证**：实现ANP协议标准的分布式身份认证方案
- **多格式接口支持**：支持OpenRPC结构化接口和自然语言接口
- **静态资源服务**：提供JSON和YAML格式的API定义文件服务

## 架构设计

### 1. 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ANP智能体服务架构                          │
├─────────────────────────────────────────────────────────────┤
│  API网关层 (FastAPI)                                         │
│  ├─ 认证中间件 (DID-WBA)                                     │
│  ├─ 路由管理                                                │
│  └─ 响应处理                                                │
├─────────────────────────────────────────────────────────────┤
│  业务逻辑层                                                  │
│  ├─ 智能体描述服务                                           │
│  ├─ API接口服务                                             │
│  └─ 静态资源服务                                             │
├─────────────────────────────────────────────────────────────┤
│  数据层                                                     │
│  ├─ 智能体元数据                                             │
│  ├─ API定义文件 (JSON/YAML)                                 │
│  └─ 安全配置                                                │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心组件

#### 2.1 主应用入口 (`src/main.py`)
- **功能**：FastAPI应用的主入口点，负责应用初始化和配置
- **责任**：
  - 创建和配置FastAPI应用实例
  - 注册中间件和路由器
  - 设置CORS策略
  - 配置异常处理器
  - 提供基础端点（根路径、健康检查等）
- **设计原则**：集中化应用配置，清晰的模块组织

#### 2.2 配置管理 (`src/config.py`)
- **功能**：集中管理应用配置和常量
- **责任**：
  - 环境变量读取和默认值设置
  - 域名和服务配置
  - JWT认证参数配置
  - API文件路径管理
  - 配置验证功能
- **设计原则**：配置与代码分离，环境适配性

#### 2.3 认证中间件 (`src/auth_middleware.py`)
- **功能**：实现DID-WBA身份认证机制
- **责任**：
  - JWT令牌验证
  - 域名验证
  - 请求授权检查
  - 豁免路径管理
- **设计原则**：框架无关的SDK封装，业务层与框架层解耦

#### 2.4 智能体描述路由器 (`src/ad_router.py`)
- **功能**：提供ANP标准的智能体描述文档
- **输出格式**：符合ANP规范的JSON文档
- **包含内容**：
  - 智能体基本信息
  - 接口定义（结构化和自然语言）
  - 安全配置
  - 服务端点信息

#### 2.5 API资源服务 (`src/api_router.py`, `src/yaml_router.py`)
- **功能**：提供静态API定义文件服务
- **支持格式**：JSON (OpenRPC) 和 YAML (OpenAPI)
- **安全机制**：文件路径验证，类型检查

## 技术实现

### 1. 技术栈

- **Web框架**：FastAPI 3.x
- **认证SDK**：octopus.anp_sdk.anp_auth
- **接口规范**：OpenRPC 1.3.2, OpenAPI 3.0.0
- **协议标准**：ANP 1.0.0
- **身份认证**：DID-WBA

### 2. 目录结构

```
/
├── src/                      # 源代码目录
│   ├── __init__.py           # 包初始化
│   ├── main.py               # FastAPI应用主入口文件
│   ├── config.py             # 配置文件和常量定义
│   ├── auth_middleware.py    # DID-WBA认证中间件
│   ├── ad_router.py          # 智能体描述路由器
│   ├── api_router.py         # JSON API文件服务
│   ├── yaml_router.py        # YAML文件服务
│   └── api/                  # API定义文件
│       ├── external-interface.json # OpenRPC接口定义
│       └── nl-interface.yaml       # 自然语言接口定义
├── docs/                     # 项目文档和密钥
│   └── jwt_key/              # JWT密钥文件
│       ├── RS256-private.pem # RSA私钥
│       └── RS256-public.pem  # RSA公钥
├── pyproject.toml            # 项目配置和依赖管理
├── uv.lock                   # uv锁定文件
├── env.example               # 环境变量示例文件
├── sepc.md                   # 项目架构设计文档
├── README.md                 # 项目说明文档
├── AGENTS.md                 # 智能体说明文档
└── LICENSE                   # 许可证文件
```

### 3. 路由设计

#### 3.1 智能体描述端点
```
GET /agents/test/ad.json
```
- **功能**：返回符合ANP规范的智能体描述
- **认证**：需要DID-WBA认证
- **响应格式**：ANP标准JSON

#### 3.2 API资源端点
```
GET /agents/test/api/{json_file}
GET /agents/test/api_files/{yaml_file}
```
- **功能**：提供API定义文件
- **认证**：需要DID-WBA认证
- **支持格式**：JSON, YAML

### 4. 安全机制

#### 4.1 DID-WBA认证流程
1. **请求拦截**：中间件检查请求路径
2. **令牌验证**：解析和验证Authorization头
3. **域名校验**：验证请求域名合法性
4. **权限检查**：确认访问权限
5. **令牌刷新**：自动处理令牌续期

#### 4.2 豁免路径配置
- 健康检查端点 (`/health`, `/v1/status`)
- API文档端点 (`/docs`, `/redoc`, `/openapi.json`)
- DID文档端点 (`/wba/user/`)
- 静态资源 (`/static/`)

## ANP协议合规性

### 1. 智能体描述规范

智能体描述文档严格遵循ANP协议规范，包含以下必需字段：

```json
{
  "protocolType": "ANP",
  "protocolVersion": "1.0.0",
  "type": "AgentDescription",
  "url": "智能体描述文档URL",
  "name": "智能体名称",
  "did": "智能体DID标识",
  "owner": "所有者信息",
  "description": "智能体描述",
  "created": "创建时间",
  "securityDefinitions": "安全定义",
  "security": "安全方案",
  "Infomations": "信息资源列表",
  "interfaces": "接口定义列表"
}
```

### 2. 接口类型支持

#### 2.1 结构化接口 (StructuredInterface)
- **协议**：OpenRPC 1.3.2
- **格式**：JSON
- **认证**：DID-WBA
- **方法示例**：
  - `calculateSum`：数值计算
  - `validateData`：数据验证
  - `generateReport`：报告生成

#### 2.2 自然语言接口 (NaturalLanguageInterface)
- **协议**：YAML (OpenAPI 3.0.0)
- **功能**：支持自然语言问答
- **特性**：SSE流式响应、会话管理
- **端点**：
  - `/api/ask`：自然语言问答
  - `/api/chat/history`：聊天历史

### 3. 安全配置

```json
{
  "securityDefinitions": {
    "didwba_sc": {
      "scheme": "didwba",
      "in": "header",
      "name": "Authorization"
    }
  },
  "security": "didwba_sc"
}
```

## 部署与配置

### 1. 环境配置

需要设置以下环境变量：

#### 必需配置
- `AGENT_DESCRIPTION_JSON_DOMAIN`：智能体描述服务域名（默认：agent-connect.ai）

#### 认证配置
- `JWT_PRIVATE_KEY_PATH`：JWT私钥文件路径
- `JWT_PUBLIC_KEY_PATH`：JWT公钥文件路径
- `JWT_ALGORITHM`：JWT算法（默认：RS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES`：访问令牌过期时间（默认：60分钟）
- `AUTH_NONCE_EXPIRY_MINUTES`：随机数过期时间（默认：5分钟）
- `AUTH_TIMESTAMP_EXPIRY_MINUTES`：时间戳过期时间（默认：5分钟）

#### 服务配置
- `HOST`：服务监听地址（默认：0.0.0.0）
- `PORT`：服务监听端口（默认：8000）
- `RELOAD`：开发模式自动重载（默认：True）
- `LOG_LEVEL`：日志级别（默认：INFO）
- `ALLOWED_ORIGINS`：CORS允许的源，逗号分隔（默认：*）

### 2. 依赖管理

使用 `uv` 进行依赖管理：
```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest

# 代码检查
uv run ruff check src tests
```

### 3. 开发调试

```bash
# 启动开发服务器（推荐：使用启动脚本）
uv run python start_anp_agent.py

# 启动开发服务器（方式二：设置PYTHONPATH）
PYTHONPATH=src uv run python src/main.py

# 启动开发服务器（方式三：使用uvicorn）
uvicorn src.main:app --reload

# 静态资源测试
uv run python -m http.server --directory src/api 9000
```

## 扩展指南

### 1. 添加新接口

1. 在 `src/api/` 目录中创建接口定义文件
2. 更新 `src/ad_router.py` 中的接口列表
3. 实现对应的API处理逻辑
4. 添加相应的测试用例

### 2. 自定义认证

1. 扩展 `src/auth_middleware.py` 中的认证逻辑
2. 添加新的豁免路径配置
3. 更新安全定义配置

### 3. 协议版本升级

1. 更新协议版本号
2. 调整智能体描述格式
3. 更新接口定义规范
4. 确保向后兼容性

## 最佳实践

### 1. 代码规范
- 遵循Google Python代码规范
- 使用类型提示和文档字符串
- 模块级日志记录配置
- 保持函数职责单一

### 2. 安全实践
- 密钥和配置分离
- 输入验证和清理
- 错误信息不泄露敏感信息
- 定期更新依赖包

### 3. 测试策略
- 单元测试覆盖率≥85%
- API端点集成测试
- 认证流程测试
- 协议合规性测试

## 参考文档

- [ANP智能体描述协议规范](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/chinese/07-ANP-%E6%99%BA%E8%83%BD%E4%BD%93%E6%8F%8F%E8%BF%B0%E5%8D%8F%E8%AE%AE%E8%A7%84%E8%8C%83(20250715)(draft).md)
- [DID-WBA身份规范](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/chinese/03-did-wba%E6%96%B9%E6%B3%95%E8%A7%84%E8%8C%83.md)
- [OpenRPC规范](https://spec.open-rpc.org/)
- [FastAPI文档](https://fastapi.tiangolo.com/)

---

*此文档为ANP智能体示例项目的技术规范，用于指导开发人员理解和扩展项目功能。*









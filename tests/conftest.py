"""
Pytest配置和共享固件

提供测试过程中需要的公共配置、客户端实例和数据
"""

import asyncio
import os

# 添加src到Python路径
import sys
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于整个测试会话"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_env_setup() -> Generator[None, None, None]:
    """设置测试环境变量"""
    original_env = os.environ.copy()

    # 设置测试环境变量
    os.environ.update({
        "AGENT_DESCRIPTION_JSON_DOMAIN": "test-agent.localhost",
        "JWT_PRIVATE_KEY_PATH": "docs/jwt_key/RS256-private.pem",
        "JWT_PUBLIC_KEY_PATH": "docs/jwt_key/RS256-public.pem",
        "LOG_LEVEL": "DEBUG"
    })

    yield

    # 恢复原始环境
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sync_client(test_env_setup) -> Generator[TestClient, None, None]:
    """同步HTTP客户端，用于简单的API测试"""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client(test_env_setup) -> AsyncGenerator[AsyncClient, None]:
    """异步HTTP客户端，用于异步API测试"""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def mock_jwt_token() -> str:
    """模拟JWT令牌用于认证测试"""
    # 这是一个简化的令牌，实际测试中应该使用真实的JWT生成
    return "Bearer test-mock-jwt-token"


@pytest.fixture
def temp_api_files() -> Generator[Path, None, None]:
    """创建临时API文件用于测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建测试用的JSON文件
        test_json = {
            "openrpc": "1.3.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "methods": []
        }
        json_file = temp_path / "test-interface.json"
        json_file.write_text('{"test": "json"}')

        # 创建测试用的YAML文件
        yaml_file = temp_path / "test-interface.yaml"
        yaml_file.write_text("test: yaml\nversion: 1.0.0")

        yield temp_path


@pytest.fixture
def expected_agent_description() -> dict:
    """期望的智能体描述格式"""
    return {
        "protocolType": "ANP",
        "protocolVersion": "1.0.0",
        "type": "AgentDescription",
        "name": "测试智能体",
        "description": str,
        "created": str,
        "securityDefinitions": {
            "didwba_sc": {
                "scheme": "didwba",
                "in": "header",
                "name": "Authorization"
            }
        },
        "security": "didwba_sc"
    }


@pytest.fixture
def exempt_paths() -> list:
    """不需要认证的路径列表"""
    return [
        "/",
        "/health",
        "/v1/status",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]

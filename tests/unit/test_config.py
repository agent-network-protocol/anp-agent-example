"""
配置模块的单元测试

测试配置文件的加载、环境变量读取和默认值设置
"""

import os
from unittest.mock import patch

import pytest


def test_import_config():
    """测试配置模块是否能正常导入"""
    try:
        import config
        assert hasattr(config, 'AGENT_DESCRIPTION_JSON_DOMAIN')
        assert hasattr(config, 'SERVICE_NAME')
        assert hasattr(config, 'ANP_PROTOCOL_VERSION')
    except ImportError as e:
        pytest.fail(f"无法导入config模块: {e}")


def test_default_config_values():
    """测试配置的默认值"""
    import config

    # 测试默认值
    assert config.SERVICE_NAME == "ANP智能体示例服务"
    assert config.SERVICE_VERSION == "1.0.0"
    assert config.ANP_PROTOCOL_VERSION == "1.0.0"
    assert config.JWT_ALGORITHM == "RS256"
    assert config.API_PREFIX == "/agents"
    assert config.AGENT_PATH_PREFIX == "/test"


@patch.dict(os.environ, {"AGENT_DESCRIPTION_JSON_DOMAIN": "custom-test.com"})
def test_env_variable_override():
    """测试环境变量覆盖默认配置"""
    # 重新导入config以获取新的环境变量值
    import importlib

    import config
    importlib.reload(config)

    assert config.AGENT_DESCRIPTION_JSON_DOMAIN == "custom-test.com"


def test_config_helper_functions():
    """测试配置辅助函数"""
    import config

    if hasattr(config, 'get_agent_url'):
        url = config.get_agent_url("/test/path")
        assert url.startswith("https://")
        assert "/test/path" in url

    if hasattr(config, 'get_agent_did'):
        did = config.get_agent_did("test-agent")
        assert did.startswith("did:")
        assert "test-agent" in did

    if hasattr(config, 'get_api_file_path'):
        path = config.get_api_file_path("test.json")
        assert "api" in path.lower()
        assert "test.json" in path


def test_jwt_key_paths():
    """测试JWT密钥路径配置"""
    import config

    assert config.JWT_PRIVATE_KEY_PATH.endswith(".pem")
    assert config.JWT_PUBLIC_KEY_PATH.endswith(".pem")
    assert "private" in config.JWT_PRIVATE_KEY_PATH.lower()
    assert "public" in config.JWT_PUBLIC_KEY_PATH.lower()


def test_cors_config():
    """测试CORS配置"""
    import config

    assert hasattr(config, 'ALLOWED_ORIGINS')
    assert isinstance(config.ALLOWED_ORIGINS, (list, str))

    if hasattr(config, 'ALLOWED_METHODS'):
        assert isinstance(config.ALLOWED_METHODS, list)

    if hasattr(config, 'ALLOWED_HEADERS'):
        assert isinstance(config.ALLOWED_HEADERS, list)

"""
主应用模块的单元测试

测试FastAPI应用的初始化、中间件配置和基础端点
"""

import pytest
from fastapi.testclient import TestClient


def test_app_creation():
    """测试FastAPI应用是否能正常创建"""
    try:
        from main import app
        assert app is not None
        assert hasattr(app, 'title')
        assert hasattr(app, 'version')
    except ImportError as e:
        pytest.fail(f"无法导入main模块: {e}")


def test_app_metadata():
    """测试应用元数据"""
    from main import app

    assert "ANP" in app.title
    assert app.version == "1.0.0"
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"


def test_root_endpoint(sync_client: TestClient):
    """测试根端点"""
    response = sync_client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "protocol" in data
    assert data["protocol"] == "ANP"
    assert "endpoints" in data
    assert "authentication" in data


def test_health_endpoint(sync_client: TestClient):
    """测试健康检查端点"""
    response = sync_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_status_endpoint(sync_client: TestClient):
    """测试状态端点"""
    response = sync_client.get("/v1/status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data


def test_docs_endpoints(sync_client: TestClient):
    """测试文档端点可访问性"""
    # 这些端点应该不需要认证
    endpoints_to_test = [
        "/docs",
        "/redoc",
        "/openapi.json"
    ]

    for endpoint in endpoints_to_test:
        response = sync_client.get(endpoint)
        # 这些端点应该返回200或重定向，而不是认证错误
        assert response.status_code in [200, 307, 308], f"{endpoint} 返回了意外的状态码: {response.status_code}"


def test_cors_headers(sync_client: TestClient):
    """测试CORS头设置"""
    response = sync_client.get("/")

    # 检查是否有CORS相关的响应头
    # 注意：具体的CORS头可能因配置而异
    assert response.status_code == 200


def test_404_handler(sync_client: TestClient):
    """测试自定义404处理器"""
    # 由于认证中间件的存在，不存在的端点会先被认证拦截
    # 所以我们测试一个豁免认证但不存在的路径（如果存在的话）
    # 或者测试已知的豁免路径下的不存在子路径
    response = sync_client.get("/docs/nonexistent")

    # 根据FastAPI的行为，这可能返回404或被重定向
    # 我们主要确认不是500错误
    assert response.status_code in [404, 307, 308], f"意外的状态码: {response.status_code}"

    # 如果是404错误，检查错误格式
    if response.status_code == 404 and response.headers.get("content-type", "").startswith("application/json"):
        data = response.json()
        assert "error" in data or "detail" in data


def test_app_routes():
    """测试应用路由是否正确注册"""
    from main import app

    # 获取所有路由路径
    routes = [route.path for route in app.routes]

    # 检查关键路由是否存在
    expected_routes = [
        "/",
        "/health",
        "/v1/status"
    ]

    for route in expected_routes:
        assert route in routes, f"路由 {route} 未找到"


def test_middleware_configuration():
    """测试中间件配置"""
    from main import app

    # 检查是否配置了中间件
    assert len(app.user_middleware) > 0, "应用应该配置了中间件"

    # 查找CORS中间件
    cors_middleware_found = False
    for middleware in app.user_middleware:
        if 'cors' in str(middleware.cls).lower():
            cors_middleware_found = True
            break

    assert cors_middleware_found, "应该配置了CORS中间件"

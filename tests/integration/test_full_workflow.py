"""
完整工作流集成测试

测试从服务启动到API调用的完整流程
"""

import pytest
from httpx import AsyncClient


class TestFullWorkflow:
    """完整工作流测试类"""

    @pytest.mark.asyncio
    async def test_service_health_check_workflow(self, async_client: AsyncClient):
        """测试服务健康检查工作流"""
        # 1. 检查服务根端点
        root_response = await async_client.get("/")
        assert root_response.status_code == 200
        root_data = root_response.json()

        # 2. 检查健康端点
        health_response = await async_client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()

        # 3. 验证版本一致性
        assert root_data.get("version") == health_data.get("version"), \
            "根端点和健康端点的版本应该一致"

        # 4. 检查状态端点
        status_response = await async_client.get("/v1/status")
        assert status_response.status_code == 200

    @pytest.mark.asyncio
    async def test_authentication_enforcement_workflow(self, async_client: AsyncClient):
        """测试认证强制执行工作流"""
        # 1. 获取智能体端点列表
        root_response = await async_client.get("/")
        assert root_response.status_code == 200
        endpoints = root_response.json().get("endpoints", {})

        # 2. 尝试访问智能体描述端点（无认证）
        if "agent_description" in endpoints:
            agent_desc_path = endpoints["agent_description"]
            # 移除域名部分，只保留路径
            if agent_desc_path.startswith("http"):
                from urllib.parse import urlparse
                agent_desc_path = urlparse(agent_desc_path).path

            agent_response = await async_client.get(agent_desc_path)
            assert agent_response.status_code == 401, "智能体描述端点应该要求认证"

        # 3. 尝试访问API资源端点（无认证）
        api_endpoints = [
            "/agents/travel/test/api/external-interface.json",
            "/agents/travel/test/api_files/nl-interface.yaml"
        ]

        for endpoint in api_endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} 应该要求认证"

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, async_client: AsyncClient):
        """测试错误处理工作流"""
        # 1. 测试不存在的端点（由于认证中间件的存在，会先返回401）
        not_found_response = await async_client.get("/nonexistent")
        # 认证中间件会首先拦截，所以期望401而不是404
        assert not_found_response.status_code == 401

        # 2. 验证错误响应格式
        if not_found_response.headers.get("content-type", "").startswith("application/json"):
            error_data = not_found_response.json()
            assert "detail" in error_data

        # 3. 测试豁免路径下的不存在端点（应该返回404或类似错误）
        docs_response = await async_client.get("/docs/nonexistent-page")
        # 这个应该不被认证拦截，可能返回404或重定向
        assert docs_response.status_code in [404, 307, 308, 200], f"意外状态码: {docs_response.status_code}"

        # 4. 测试方法不允许
        post_response = await async_client.post("/")
        # 根端点可能不支持POST
        assert post_response.status_code in [405, 422], "根端点应该限制HTTP方法"

    @pytest.mark.asyncio
    async def test_documentation_accessibility_workflow(self, async_client: AsyncClient):
        """测试文档访问性工作流"""
        # 1. 检查OpenAPI规范
        openapi_response = await async_client.get("/openapi.json")
        assert openapi_response.status_code == 200

        openapi_data = openapi_response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data

        # 2. 检查Swagger UI
        docs_response = await async_client.get("/docs")
        assert docs_response.status_code == 200

        # 3. 检查ReDoc
        redoc_response = await async_client.get("/redoc")
        assert redoc_response.status_code == 200

        # 4. 验证文档中包含关键路径
        paths = openapi_data.get("paths", {})
        expected_paths = ["/", "/health"]
        for path in expected_paths:
            assert path in paths, f"OpenAPI规范中应该包含路径 {path}"

    @pytest.mark.asyncio
    async def test_cors_integration(self, async_client: AsyncClient):
        """测试CORS集成"""
        # 测试预检请求
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }

        # OPTIONS请求用于预检
        options_response = await async_client.options("/", headers=headers)

        # 根据CORS配置，应该允许跨域访问
        # 状态码可能是200或者405，取决于具体实现
        assert options_response.status_code in [200, 405]

    @pytest.mark.asyncio
    async def test_service_consistency_workflow(self, async_client: AsyncClient):
        """测试服务一致性工作流"""
        # 1. 多次调用根端点，验证响应一致性
        responses = []
        for _ in range(3):
            response = await async_client.get("/")
            assert response.status_code == 200
            responses.append(response.json())

        # 验证多次响应的一致性（除了可能变化的时间戳）
        first_response = responses[0]
        for response in responses[1:]:
            assert response.get("service") == first_response.get("service")
            assert response.get("version") == first_response.get("version")
            assert response.get("protocol") == first_response.get("protocol")

        # 2. 验证不同健康检查端点的一致性
        health_response = await async_client.get("/health")
        status_response = await async_client.get("/v1/status")

        assert health_response.status_code == 200
        assert status_response.status_code == 200

        health_data = health_response.json()
        status_data = status_response.json()

        # 服务名称应该一致（如果两个端点都返回）
        if "service" in health_data and "service" in status_data:
            # 注意：字段名可能不同，所以我们检查是否都表示服务正常
            assert health_data.get("status") == "healthy"
            assert status_data.get("status") == "ok"

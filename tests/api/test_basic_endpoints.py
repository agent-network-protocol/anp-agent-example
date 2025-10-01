"""
基础API端点测试

测试不需要认证的基础端点功能
"""

import pytest
from httpx import AsyncClient


class TestBasicEndpoints:
    """基础端点测试类"""

    @pytest.mark.asyncio
    async def test_root_endpoint_async(self, async_client: AsyncClient):
        """异步测试根端点"""
        response = await async_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["protocol"] == "ANP"
        assert data["protocol_version"] == "1.0.0"
        assert "endpoints" in data
        assert "agent_description" in data["endpoints"]

    @pytest.mark.asyncio
    async def test_health_endpoint_response_format(self, async_client: AsyncClient):
        """测试健康检查端点的响应格式"""
        response = await async_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        required_fields = ["status", "service", "version"]
        for field in required_fields:
            assert field in data, f"响应中缺少必需字段: {field}"

        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_status_endpoint_response_format(self, async_client: AsyncClient):
        """测试状态端点的响应格式"""
        response = await async_client.get("/v1/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_openapi_spec(self, async_client: AsyncClient):
        """测试OpenAPI规范端点"""
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

        # 检查基础路径是否存在于OpenAPI规范中
        paths = data["paths"]
        assert "/" in paths
        assert "/health" in paths

    @pytest.mark.asyncio
    async def test_docs_accessibility(self, async_client: AsyncClient):
        """测试文档页面的可访问性"""
        docs_response = await async_client.get("/docs")
        # Swagger UI通常返回HTML，状态码应该是200
        assert docs_response.status_code == 200

        redoc_response = await async_client.get("/redoc")
        # ReDoc也应该返回HTML，状态码应该是200
        assert redoc_response.status_code == 200

    @pytest.mark.asyncio
    async def test_content_type_headers(self, async_client: AsyncClient):
        """测试响应的Content-Type头"""
        response = await async_client.get("/")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        health_response = await async_client.get("/health")
        assert health_response.status_code == 200
        assert "application/json" in health_response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_response_time(self, async_client: AsyncClient):
        """测试响应时间（简单的性能检查）"""
        import time

        start_time = time.time()
        response = await async_client.get("/")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time
        # 响应时间应该在合理范围内（小于1秒）
        assert response_time < 1.0, f"响应时间过长: {response_time}秒"

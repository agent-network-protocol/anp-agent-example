"""
身份验证中间件测试

测试DID-WBA认证中间件的功能
"""

import pytest
from httpx import AsyncClient


class TestAuthMiddleware:
    """身份验证中间件测试类"""

    @pytest.mark.asyncio
    async def test_exempt_paths_no_auth_required(self, async_client: AsyncClient, exempt_paths: list):
        """测试豁免路径不需要认证"""
        for path in exempt_paths:
            response = await async_client.get(path)
            # 豁免路径应该返回200而不是401
            assert response.status_code != 401, f"豁免路径 {path} 意外要求认证"
            # 根据端点不同，可能返回200, 404等，但不应该是401
            assert response.status_code in [200, 404, 307, 308], f"豁免路径 {path} 返回意外状态码: {response.status_code}"

    @pytest.mark.asyncio
    async def test_protected_paths_require_auth(self, async_client: AsyncClient):
        """测试受保护的路径需要认证"""
        protected_paths = [
            "/agents/test/ad.json",
            "/agents/test/api/external-interface.json",
            "/agents/test/api_files/nl-interface.yaml"
        ]

        for path in protected_paths:
            response = await async_client.get(path)
            # 受保护路径应该返回401未认证错误
            assert response.status_code == 401, f"受保护路径 {path} 未要求认证，返回状态码: {response.status_code}"

    @pytest.mark.asyncio
    async def test_invalid_auth_header_formats(self, async_client: AsyncClient):
        """测试无效的认证头格式"""
        invalid_headers = [
            {},  # 无认证头
            {"Authorization": ""},  # 空认证头
            {"Authorization": "InvalidFormat"},  # 无效格式
            {"Authorization": "Basic dGVzdA=="},  # 错误的认证方案
            {"Authorization": "Bearer"},  # 缺少令牌
            {"Authorization": "Bearer "},  # 空令牌
        ]

        test_path = "/agents/test/ad.json"

        for headers in invalid_headers:
            response = await async_client.get(test_path, headers=headers)
            assert response.status_code == 401, f"无效认证头 {headers} 未被正确拒绝"

    @pytest.mark.asyncio
    async def test_malformed_jwt_token(self, async_client: AsyncClient):
        """测试格式错误的JWT令牌"""
        malformed_tokens = [
            "Bearer invalid.token.format",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # 不完整的JWT
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",  # 无效的payload
            "Bearer not.a.jwt.at.all",  # 完全不是JWT格式
        ]

        test_path = "/agents/test/ad.json"

        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = await async_client.get(test_path, headers=headers)
            assert response.status_code == 401, f"格式错误的令牌 {token} 未被正确拒绝"

    @pytest.mark.asyncio
    async def test_auth_middleware_error_responses(self, async_client: AsyncClient):
        """测试认证中间件的错误响应格式"""
        response = await async_client.get("/agents/test/ad.json")
        assert response.status_code == 401

        # 检查错误响应格式
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            # 检查是否包含错误信息
            assert "error" in data or "detail" in data or "message" in data

    @pytest.mark.asyncio
    async def test_case_insensitive_authorization_header(self, async_client: AsyncClient):
        """测试Authorization头的大小写不敏感性"""
        test_path = "/agents/test/ad.json"

        # 测试不同的大小写组合
        header_variations = [
            {"authorization": "Bearer test-token"},  # 全小写
            {"Authorization": "Bearer test-token"},  # 标准格式
            {"AUTHORIZATION": "Bearer test-token"},  # 全大写
        ]

        for headers in header_variations:
            response = await async_client.get(test_path, headers=headers)
            # 所有变体都应该被识别为认证尝试（虽然令牌无效）
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_multiple_authorization_headers(self, async_client: AsyncClient):
        """测试多个Authorization头的处理"""
        test_path = "/agents/test/ad.json"

        # httpx通常不允许重复头，但我们可以测试头值包含多个值的情况
        headers = {"Authorization": "Bearer token1, Bearer token2"}
        response = await async_client.get(test_path, headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_middleware_with_query_parameters(self, async_client: AsyncClient):
        """测试带查询参数的认证请求"""
        test_path = "/agents/test/ad.json?param=value&another=test"

        response = await async_client.get(test_path)
        # 即使有查询参数，认证仍然是必需的
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_middleware_preserves_path_info(self, async_client: AsyncClient):
        """测试认证中间件保持路径信息的完整性"""
        # 测试路径中的特殊字符
        special_paths = [
            "/agents/test/api/file%20with%20spaces.json",
            "/agents/test/api/file-with-dashes.json",
            "/agents/test/api/file_with_underscores.json"
        ]

        for path in special_paths:
            response = await async_client.get(path)
            # 所有路径都应该先检查认证
            assert response.status_code == 401

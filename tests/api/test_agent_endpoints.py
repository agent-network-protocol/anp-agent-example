"""
智能体相关端点测试

测试需要认证的智能体描述和API资源端点
"""

import pytest
from httpx import AsyncClient


class TestAgentEndpoints:
    """智能体端点测试类"""

    @pytest.mark.asyncio
    async def test_agent_description_without_auth(self, async_client: AsyncClient):
        """测试未认证访问智能体描述端点应返回401"""
        response = await async_client.get("/agents/travel/test/ad.json")
        # 应该返回未授权错误
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_api_json_file_without_auth(self, async_client: AsyncClient):
        """测试未认证访问JSON API文件应返回401"""
        response = await async_client.get("/agents/travel/test/api/external-interface.json")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_api_yaml_file_without_auth(self, async_client: AsyncClient):
        """测试未认证访问YAML API文件应返回401"""
        response = await async_client.get("/agents/travel/test/api_files/nl-interface.yaml")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_agent_description_with_mock_auth(self, async_client: AsyncClient, mock_jwt_token: str):
        """使用模拟认证测试智能体描述端点（可能失败，用于发现认证问题）"""
        headers = {"Authorization": mock_jwt_token}
        response = await async_client.get("/agents/travel/test/ad.json", headers=headers)

        # 这里可能返回401（认证失败）或200（认证成功）
        # 我们记录结果以便后续分析
        print(f"智能体描述端点响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"成功获取智能体描述: {data}")
        elif response.status_code == 401:
            print("模拟认证失败，这是预期的")
        else:
            print(f"意外的状态码: {response.status_code}, 响应: {response.text}")

    @pytest.mark.asyncio
    async def test_json_api_file_access(self, async_client: AsyncClient):
        """测试JSON API文件访问"""
        # 先测试不存在的文件
        response = await async_client.get("/agents/travel/test/api/nonexistent.json")
        # 应该返回401（未认证）而不是404，因为认证在前
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_yaml_api_file_access(self, async_client: AsyncClient):
        """测试YAML API文件访问"""
        # 测试不存在的文件
        response = await async_client.get("/agents/travel/test/api_files/nonexistent.yaml")
        # 应该返回401（未认证）
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_agent_endpoints_path_validation(self, async_client: AsyncClient):
        """测试智能体端点的路径验证"""
        # 测试错误的路径格式
        invalid_paths = [
            "/agents/travel/test/ad.xml",  # 错误的文件扩展名
            "/agents/travel/test/api/",    # 缺少文件名
            "/agents/travel/test/api_files/",  # 缺少文件名
            "/agents/wrong/path/ad.json",  # 错误的路径
        ]

        for path in invalid_paths:
            response = await async_client.get(path)
            # 应该返回404或401，取决于路由匹配情况
            assert response.status_code in [401, 404], f"路径 {path} 返回了意外状态码: {response.status_code}"

    @pytest.mark.asyncio
    async def test_agent_endpoints_methods(self, async_client: AsyncClient):
        """测试智能体端点只接受GET方法"""
        endpoints = [
            "/agents/travel/test/ad.json",
            "/agents/travel/test/api/external-interface.json",
            "/agents/travel/test/api_files/nl-interface.yaml"
        ]

        for endpoint in endpoints:
            # 测试POST方法应该被拒绝
            post_response = await async_client.post(endpoint)
            assert post_response.status_code in [401, 405], f"{endpoint} POST请求返回意外状态码"

            # 测试PUT方法应该被拒绝
            put_response = await async_client.put(endpoint)
            assert put_response.status_code in [401, 405], f"{endpoint} PUT请求返回意外状态码"

            # 测试DELETE方法应该被拒绝
            delete_response = await async_client.delete(endpoint)
            assert delete_response.status_code in [401, 405], f"{endpoint} DELETE请求返回意外状态码"

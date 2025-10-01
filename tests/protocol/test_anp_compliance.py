"""
ANP协议合规性测试

验证服务是否符合ANP协议规范要求
"""

import json

import pytest
from httpx import AsyncClient


class TestANPCompliance:
    """ANP协议合规性测试类"""

    @pytest.mark.asyncio
    async def test_root_endpoint_anp_info(self, async_client: AsyncClient):
        """测试根端点包含正确的ANP协议信息"""
        response = await async_client.get("/")
        assert response.status_code == 200

        data = response.json()

        # 验证ANP协议信息
        assert data.get("protocol") == "ANP", "协议类型应该是ANP"
        assert data.get("protocol_version") == "1.0.0", "协议版本应该是1.0.0"

        # 验证服务信息
        assert "service" in data, "应该包含服务名称"
        assert "version" in data, "应该包含服务版本"
        assert "description" in data, "应该包含服务描述"

        # 验证端点信息
        assert "endpoints" in data, "应该包含端点信息"
        endpoints = data["endpoints"]
        assert "agent_description" in endpoints, "应该包含智能体描述端点"
        assert "api_resources" in endpoints, "应该包含API资源端点"

        # 验证认证信息
        assert data.get("authentication") == "DID-WBA", "应该使用DID-WBA认证"

    def test_expected_agent_description_format(self, expected_agent_description: dict):
        """测试期望的智能体描述格式是否符合ANP规范"""
        # 验证必需的ANP字段
        required_fields = [
            "protocolType", "protocolVersion", "type", "name",
            "description", "created", "securityDefinitions", "security"
        ]

        for field in required_fields:
            assert field in expected_agent_description, f"智能体描述应该包含 {field} 字段"

        # 验证协议信息
        assert expected_agent_description["protocolType"] == "ANP"
        assert expected_agent_description["protocolVersion"] == "1.0.0"
        assert expected_agent_description["type"] == "AgentDescription"

        # 验证安全配置
        security_defs = expected_agent_description["securityDefinitions"]
        assert "didwba_sc" in security_defs, "应该定义DID-WBA安全方案"

        didwba_def = security_defs["didwba_sc"]
        assert didwba_def["scheme"] == "didwba", "安全方案应该是didwba"
        assert didwba_def["in"] == "header", "认证信息应该在header中"
        assert didwba_def["name"] == "Authorization", "认证头应该是Authorization"

        assert expected_agent_description["security"] == "didwba_sc", "应该使用didwba_sc安全方案"

    @pytest.mark.asyncio
    async def test_api_file_structure_compliance(self, async_client: AsyncClient):
        """测试API文件结构是否符合规范（通过错误响应推断）"""
        # 由于没有认证，我们无法获取实际文件内容
        # 但我们可以验证端点结构是否符合ANP规范要求

        expected_api_endpoints = [
            "/agents/travel/test/api/external-interface.json",
            "/agents/travel/test/api_files/nl-interface.yaml"
        ]

        for endpoint in expected_api_endpoints:
            response = await async_client.get(endpoint)
            # 应该因为认证失败返回401，而不是404（证明端点存在）
            assert response.status_code == 401, f"端点 {endpoint} 应该存在但需要认证"

    @pytest.mark.asyncio
    async def test_anp_agent_path_structure(self, async_client: AsyncClient):
        """测试ANP智能体路径结构是否正确"""
        # ANP规范要求智能体描述路径格式为 /agents/{domain}/{name}/ad.json
        agent_description_path = "/agents/travel/test/ad.json"

        response = await async_client.get(agent_description_path)
        # 应该返回401（需要认证）而不是404（路径不存在）
        assert response.status_code == 401, "智能体描述路径应该存在但需要认证"

    @pytest.mark.asyncio
    async def test_http_methods_compliance(self, async_client: AsyncClient):
        """测试HTTP方法使用是否符合ANP规范"""
        anp_endpoints = [
            "/agents/travel/test/ad.json",
            "/agents/travel/test/api/external-interface.json",
            "/agents/travel/test/api_files/nl-interface.yaml"
        ]

        for endpoint in anp_endpoints:
            # GET方法应该被支持（虽然需要认证）
            get_response = await async_client.get(endpoint)
            assert get_response.status_code == 401, f"{endpoint} 应该支持GET方法"

            # POST方法通常不应该被ANP端点支持
            post_response = await async_client.post(endpoint)
            assert post_response.status_code in [401, 405], f"{endpoint} 不应该支持POST方法"

            # PUT和DELETE也不应该被支持
            put_response = await async_client.put(endpoint)
            assert put_response.status_code in [401, 405], f"{endpoint} 不应该支持PUT方法"

            delete_response = await async_client.delete(endpoint)
            assert delete_response.status_code in [401, 405], f"{endpoint} 不应该支持DELETE方法"

    @pytest.mark.asyncio
    async def test_content_type_requirements(self, async_client: AsyncClient):
        """测试内容类型要求"""
        # 基础端点应该返回JSON
        json_endpoints = ["/", "/health", "/v1/status"]

        for endpoint in json_endpoints:
            response = await async_client.get(endpoint)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                assert "application/json" in content_type, f"{endpoint} 应该返回JSON内容"

    @pytest.mark.asyncio
    async def test_anp_error_response_format(self, async_client: AsyncClient):
        """测试ANP错误响应格式"""
        # 测试认证错误响应
        response = await async_client.get("/agents/travel/test/ad.json")
        assert response.status_code == 401

        # 检查是否返回了有意义的错误信息
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                error_data = response.json()
                # 错误响应应该包含有用的信息
                assert any(key in error_data for key in ["error", "detail", "message"]), \
                    "错误响应应该包含错误信息"
            except json.JSONDecodeError:
                pytest.fail("认证错误应该返回有效的JSON响应")

    @pytest.mark.asyncio
    async def test_security_headers(self, async_client: AsyncClient):
        """测试安全头设置"""
        response = await async_client.get("/")
        assert response.status_code == 200

        headers = response.headers

        # 检查一些常见的安全头（可选，但推荐）
        # 注意：这些头的存在取决于具体的安全配置
        security_headers_to_check = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]

        # 记录安全头的存在情况，用于安全审查
        for header in security_headers_to_check:
            header_value = headers.get(header)
            print(f"安全头 {header}: {header_value if header_value else '未设置'}")

    @pytest.mark.asyncio
    async def test_anp_version_consistency(self, async_client: AsyncClient):
        """测试ANP版本一致性"""
        response = await async_client.get("/")
        assert response.status_code == 200

        data = response.json()
        protocol_version = data.get("protocol_version")

        # ANP版本应该是1.0.0
        assert protocol_version == "1.0.0", f"ANP版本应该是1.0.0，但得到 {protocol_version}"

        # 检查OpenAPI规范中的版本信息
        openapi_response = await async_client.get("/openapi.json")
        if openapi_response.status_code == 200:
            openapi_data = openapi_response.json()
            api_version = openapi_data.get("info", {}).get("version")
            print(f"OpenAPI版本: {api_version}")

            # API版本应该与服务版本一致
            service_version = data.get("version")
            if api_version and service_version:
                assert api_version == service_version, "OpenAPI版本应该与服务版本一致"

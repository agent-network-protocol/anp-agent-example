#!/usr/bin/env python3
"""JSON-RPC API测试示例

这个脚本展示如何调用ANP智能体的JSON-RPC接口，包括内联接口和外部接口的所有方法。
"""

import asyncio
import json
import uuid
from typing import Any, Dict

import httpx


class JsonRpcClient:
    """JSON-RPC 2.0客户端"""

    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.session = httpx.AsyncClient()

    async def close(self):
        """关闭HTTP客户端"""
        await self.session.aclose()

    async def call_method(self, endpoint: str, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用JSON-RPC方法"""
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id
        }

        if params:
            payload["params"] = params

        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        url = f"{self.base_url}{endpoint}"
        print(f"\n🔧 调用方法: {method}")
        print(f"📍 端点: {url}")
        print(f"📤 请求: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        try:
            response = await self.session.post(url, json=payload, headers=headers)
            result = response.json()
            print(f"📥 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            return {"error": str(e)}


async def test_inline_interface(client: JsonRpcClient):
    """测试内联OpenRPC接口（echo和getStatus方法）"""
    print("\n" + "="*60)
    print("🚀 测试内联OpenRPC接口")
    print("="*60)

    # 测试echo方法
    echo_result = await client.call_method(
        "/api/test/jsonrpc",
        "echo",
        {"message": "Hello ANP Agent!"}
    )

    # 测试getStatus方法
    status_result = await client.call_method(
        "/api/test/jsonrpc",
        "getStatus"
    )

    return echo_result, status_result


async def test_external_interface(client: JsonRpcClient):
    """测试外部OpenRPC接口（calculateSum、validateData、generateReport方法）"""
    print("\n" + "="*60)
    print("🌐 测试外部OpenRPC接口")
    print("="*60)

    # 测试calculateSum方法
    sum_result = await client.call_method(
        "/api/external/jsonrpc",
        "calculateSum",
        {"numbers": [1, 2, 3, 4, 5, 10.5, 20.3]}
    )

    # 测试validateData方法
    validation_result = await client.call_method(
        "/api/external/jsonrpc",
        "validateData",
        {
            "data": {
                "email": "test@example.com",
                "phone": "+1234567890",
                "age": 25,
                "name": "张三"
            }
        }
    )

    # 测试generateReport方法
    report_result = await client.call_method(
        "/api/external/jsonrpc",
        "generateReport",
        {
            "reportRequest": {
                "title": "ANP智能体测试报告",
                "content": "这是一个测试报告内容，展示了智能体的各项功能测试结果。",
                "metadata": {
                    "author": "ANP测试系统",
                    "audience": ["开发者", "测试人员"],
                    "tags": ["测试", "ANP", "智能体"],
                    "published": True
                }
            },
            "format": "markdown"
        }
    )

    return sum_result, validation_result, report_result


async def test_error_cases(client: JsonRpcClient):
    """测试错误情况"""
    print("\n" + "="*60)
    print("⚠️  测试错误情况")
    print("="*60)

    # 测试不存在的方法
    print("\n📝 测试不存在的方法:")
    await client.call_method("/api/test/jsonrpc", "unknownMethod")

    # 测试参数错误
    print("\n📝 测试echo方法参数错误:")
    await client.call_method("/api/test/jsonrpc", "echo", {"wrong_param": "test"})

    # 测试calculateSum参数错误
    print("\n📝 测试calculateSum参数错误:")
    await client.call_method("/api/external/jsonrpc", "calculateSum", {"numbers": "not_an_array"})

    # 测试空数组
    print("\n📝 测试calculateSum空数组:")
    await client.call_method("/api/external/jsonrpc", "calculateSum", {"numbers": []})


async def main():
    """主测试函数"""
    # 配置
    base_url = "http://localhost:8000"

    print("🤖 ANP智能体JSON-RPC接口测试")
    print(f"🌐 服务地址: {base_url}")
    print(f"📋 测试项目: 内联接口、外部接口、错误处理")

    # 创建客户端
    client = JsonRpcClient(base_url)

    try:
        # 测试内联接口
        echo_result, status_result = await test_inline_interface(client)

        # 测试外部接口
        sum_result, validation_result, report_result = await test_external_interface(client)

        # 测试错误情况
        await test_error_cases(client)

        # 总结
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)

        success_count = 0
        total_count = 5

        if echo_result.get("result"):
            print("✅ echo方法测试成功")
            success_count += 1
        else:
            print("❌ echo方法测试失败")

        if status_result.get("result"):
            print("✅ getStatus方法测试成功")
            success_count += 1
        else:
            print("❌ getStatus方法测试失败")

        if sum_result.get("result"):
            print("✅ calculateSum方法测试成功")
            success_count += 1
        else:
            print("❌ calculateSum方法测试失败")

        if validation_result.get("result"):
            print("✅ validateData方法测试成功")
            success_count += 1
        else:
            print("❌ validateData方法测试失败")

        if report_result.get("result"):
            print("✅ generateReport方法测试成功")
            success_count += 1
        else:
            print("❌ generateReport方法测试失败")

        print(f"\n🎯 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    finally:
        await client.close()


if __name__ == "__main__":
    print("开始运行ANP智能体JSON-RPC接口测试...")
    print("请确保智能体服务已启动在 http://localhost:8000")
    print("启动命令: python main.py 或 uvicorn main:app --reload")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {str(e)}")
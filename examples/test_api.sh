#!/bin/bash

# ANP智能体JSON-RPC API测试脚本
# 使用curl命令测试所有的JSON-RPC接口

BASE_URL="http://localhost:8000"
CONTENT_TYPE="Content-Type: application/json"

echo "🤖 ANP智能体JSON-RPC接口测试"
echo "🌐 服务地址: $BASE_URL"
echo "========================================"

# 测试内联接口

echo ""
echo "🚀 测试内联OpenRPC接口"
echo "========================================"

echo ""
echo "📝 测试echo方法:"
curl -X POST "$BASE_URL/api/test/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "echo",
    "params": {
      "message": "Hello ANP Agent from curl!"
    },
    "id": "test-echo-1"
  }' | jq '.'

echo ""
echo "📝 测试getStatus方法:"
curl -X POST "$BASE_URL/api/test/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "getStatus",
    "id": "test-status-1"
  }' | jq '.'

# 测试外部接口

echo ""
echo ""
echo "🌐 测试外部OpenRPC接口"
echo "========================================"

echo ""
echo "📝 测试calculateSum方法:"
curl -X POST "$BASE_URL/api/external/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "calculateSum",
    "params": {
      "numbers": [1, 2, 3, 4, 5, 10.5, 20.3]
    },
    "id": "test-sum-1"
  }' | jq '.'

echo ""
echo "📝 测试validateData方法:"
curl -X POST "$BASE_URL/api/external/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "validateData",
    "params": {
      "data": {
        "email": "test@example.com",
        "phone": "+1234567890",
        "age": 25,
        "name": "张三"
      }
    },
    "id": "test-validate-1"
  }' | jq '.'

echo ""
echo "📝 测试generateReport方法:"
curl -X POST "$BASE_URL/api/external/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "generateReport",
    "params": {
      "reportRequest": {
        "title": "ANP智能体测试报告",
        "content": "这是一个测试报告内容，展示了智能体的各项功能测试结果。",
        "metadata": {
          "author": "ANP测试系统",
          "audience": ["开发者", "测试人员"],
          "tags": ["测试", "ANP", "智能体"],
          "published": true
        }
      },
      "format": "markdown"
    },
    "id": "test-report-1"
  }' | jq '.'

# 测试错误情况

echo ""
echo ""
echo "⚠️  测试错误情况"
echo "========================================"

echo ""
echo "📝 测试不存在的方法:"
curl -X POST "$BASE_URL/api/test/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "unknownMethod",
    "id": "test-error-1"
  }' | jq '.'

echo ""
echo "📝 测试echo方法参数错误:"
curl -X POST "$BASE_URL/api/test/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "echo",
    "params": {
      "wrong_param": "test"
    },
    "id": "test-error-2"
  }' | jq '.'

echo ""
echo "📝 测试calculateSum参数错误:"
curl -X POST "$BASE_URL/api/external/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "calculateSum",
    "params": {
      "numbers": "not_an_array"
    },
    "id": "test-error-3"
  }' | jq '.'

echo ""
echo ""
echo "✅ 测试完成!"
echo "如果所有请求都返回了结果，说明API实现正常工作。"
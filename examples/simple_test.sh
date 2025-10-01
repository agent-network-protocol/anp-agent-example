#!/bin/bash

# ANP智能体JSON-RPC API简单测试脚本

BASE_URL="http://localhost:8000"
CONTENT_TYPE="Content-Type: application/json"

echo "🤖 ANP智能体JSON-RPC接口测试"
echo "========================================"

echo ""
echo "📝 测试内联接口 - echo方法:"
curl -s -X POST "$BASE_URL/api/test/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"echo","params":{"message":"Hello"},"id":"test1"}'
echo ""

echo ""
echo "📝 测试内联接口 - getStatus方法:"
curl -s -X POST "$BASE_URL/api/test/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"getStatus","id":"test2"}'
echo ""

echo ""
echo "📝 测试外部接口 - calculateSum方法:"
curl -s -X POST "$BASE_URL/api/external/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"calculateSum","params":{"numbers":[1,2,3,4,5]},"id":"test3"}'
echo ""

echo ""
echo "📝 测试外部接口 - validateData方法:"
curl -s -X POST "$BASE_URL/api/external/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"validateData","params":{"data":{"email":"test@example.com","age":25}},"id":"test4"}'
echo ""

echo ""
echo "📝 测试外部接口 - generateReport方法:"
curl -s -X POST "$BASE_URL/api/external/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"generateReport","params":{"reportRequest":{"title":"测试报告","content":"测试内容"},"format":"markdown"},"id":"test5"}'
echo ""

echo ""
echo "📝 测试错误情况 - 不存在的方法:"
curl -s -X POST "$BASE_URL/api/test/jsonrpc" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"unknownMethod","id":"test6"}'
echo ""

echo ""
echo "✅ 所有测试完成!"
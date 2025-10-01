#!/bin/bash

# ANP智能体统一JSON-RPC API简单测试脚本

BASE_URL="http://localhost:8000"
ENDPOINT="/agents/test/jsonrpc"
CONTENT_TYPE="Content-Type: application/json"

echo "🤖 ANP智能体统一JSON-RPC接口测试"
echo "🌐 端点: $BASE_URL$ENDPOINT"
echo "========================================"

echo ""
echo "📝 测试echo方法:"
curl -s -X POST "$BASE_URL$ENDPOINT" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"echo","params":{"message":"Hello"},"id":"test1"}'
echo ""

echo ""
echo "📝 测试getStatus方法:"
curl -s -X POST "$BASE_URL$ENDPOINT" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"getStatus","id":"test2"}'
echo ""

echo ""
echo "📝 测试add方法:"
curl -s -X POST "$BASE_URL$ENDPOINT" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"add","params":{"a":5,"b":3},"id":"test3"}'
echo ""

echo ""
echo "📝 测试greet方法:"
curl -s -X POST "$BASE_URL$ENDPOINT" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"greet","params":{"name":"张三"},"id":"test4"}'
echo ""

echo ""
echo "📝 测试错误情况 - 不存在的方法:"
curl -s -X POST "$BASE_URL$ENDPOINT" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"unknownMethod","id":"test5"}'
echo ""

echo ""
echo "📝 测试add方法参数错误:"
curl -s -X POST "$BASE_URL$ENDPOINT" \
  -H "$CONTENT_TYPE" \
  -d '{"jsonrpc":"2.0","method":"add","params":{"a":"not_a_number","b":3},"id":"test6"}'
echo ""

echo ""
echo "✅ 所有测试完成!"
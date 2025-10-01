"""Agent Description Router for ANP-compliant agent metadata.

This module provides the agent description endpoint that returns metadata
about the test agent following the ANP protocol specification.
"""

import logging
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import get_agent_did, get_agent_url, settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents")

@router.get("/travel/test/ad.json")
async def get_test_agent_description():
    """
    提供测试智能体的描述信息（符合ANP规范）
    
    Returns:
        测试智能体描述的ANP格式JSON
    """
    try:
        # 创建符合ANP规范的测试智能体描述
        test_agent = {
            "protocolType": "ANP",
            "protocolVersion": "1.0.0",
            "type": "AgentDescription",
            "url": get_agent_url("/agents/travel/test/ad.json"),
            "name": "测试智能体",
            "did": get_agent_did("test-agent"),
            "owner": {
                "type": "Organization",
                "name": settings.agent_domain,
                "url": f"https://{settings.agent_domain}"
            },
            "description": "测试智能体，用于演示ANP协议规范的实现，提供基础的测试服务和接口示例。",
            "created": datetime.utcnow().isoformat() + "Z",
            "securityDefinitions": {
                "didwba_sc": {
                    "scheme": "didwba",
                    "in": "header",
                    "name": "Authorization"
                }
            },
            "security": "didwba_sc",
            "Infomations": [
                {
                    "type": "Information",
                    "description": "测试智能体的基本信息和服务说明",
                    "url": get_agent_url("/agents/travel/test/info/basic-info.json")
                },
                {
                    "type": "Product",
                    "description": "测试产品信息，用于演示产品描述规范",
                    "url": get_agent_url("/agents/travel/test/products/test-product.json")
                }
            ],
            "interfaces": [
                {
                    "type": "StructuredInterface",
                    "protocol": "openrpc",
                    "version": "1.3.2",
                    "url": get_agent_url("/agents/travel/test/api/external-interface.json"),
                    "description": "外部OpenRPC接口，提供测试智能体的基础服务API"
                },
                {
                    "type": "StructuredInterface",
                    "protocol": "openrpc",
                    "version": "1.3.2",
                    "description": "内联OpenRPC接口，提供测试智能体的高级服务",
                    "content": {
                        "openrpc": "1.3.2",
                        "info": {
                            "title": "Test Agent Inline API",
                            "version": "1.0.0",
                            "description": "内联的测试智能体API，提供基础的测试方法和示例",
                            "x-anp-protocol-type": "ANP",
                            "x-anp-protocol-version": "1.0.0"
                        },
                        "security": [
                            {
                                "didwba": []
                            }
                        ],
                        "servers": [
                            {
                                "name": "Test Server",
                                "url": get_agent_url("/api/test/jsonrpc"),
                                "description": "测试智能体API服务器"
                            }
                        ],
                        "methods": [
                            {
                                "name": "echo",
                                "summary": "回声测试",
                                "description": "返回输入的消息，用于测试连接和基础功能",
                                "params": [
                                    {
                                        "name": "message",
                                        "description": "要回声的消息内容",
                                        "required": True,
                                        "schema": {
                                            "type": "string",
                                            "minLength": 1,
                                            "maxLength": 1000,
                                            "description": "输入的文本消息"
                                        }
                                    }
                                ],
                                "result": {
                                    "name": "echoResult",
                                    "description": "回声结果",
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "originalMessage": {
                                                "type": "string",
                                                "description": "原始输入消息"
                                            },
                                            "response": {
                                                "type": "string",
                                                "description": "回声响应"
                                            },
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                                "description": "响应时间戳"
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "name": "getStatus",
                                "summary": "获取系统状态",
                                "description": "获取测试智能体的当前运行状态和基本信息",
                                "params": [],
                                "result": {
                                    "name": "statusResult",
                                    "description": "系统状态信息",
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "enum": ["online", "offline", "maintenance"],
                                                "description": "服务状态"
                                            },
                                            "version": {
                                                "type": "string",
                                                "description": "服务版本"
                                            },
                                            "uptime": {
                                                "type": "integer",
                                                "description": "运行时间（秒）"
                                            },
                                            "capabilities": {
                                                "type": "array",
                                                "items": {
                                                    "type": "string"
                                                },
                                                "description": "支持的功能列表"
                                            }
                                        }
                                    }
                                }
                            }
                        ],
                        "components": {
                            "securitySchemes": {
                                "didwba": {
                                    "type": "http",
                                    "scheme": "bearer",
                                    "bearerFormat": "DID-WBA",
                                    "description": "DID-WBA认证方案"
                                }
                            }
                        }
                    }
                },
                {
                    "type": "NaturalLanguageInterface",
                    "protocol": "YAML",
                    "version": "1.0.0",
                    "url": get_agent_url("/agents/travel/test/api/nl-interface.yaml"),
                    "description": "自然语言接口，支持与测试智能体进行对话交互"
                }
            ]
        }

        logger.info("Successfully generated test agent description")
        return JSONResponse(content=test_agent)

    except Exception as e:
        logger.error(f"Error generating test agent description: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "message": str(e)}
        )

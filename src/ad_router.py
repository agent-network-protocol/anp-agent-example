"""Agent Description Router for ANP-compliant agent metadata.

This module exposes JSON endpoints that describe the demo ANP agent and
provide supporting test data payloads used by downstream services.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from config import (
    AGENT_DESCRIPTION_JSON_DOMAIN,
    AGENT_PATH_PREFIX,
    API_PREFIX,
    get_agent_did,
    get_agent_url,
    settings,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agent Description"])

_AGENT_BASE_PATH = f"{API_PREFIX}{AGENT_PATH_PREFIX}"
_EXTERNAL_INTERFACE_PATH = f"{_AGENT_BASE_PATH}/api/external-interface.json"
_INFO_PATH_TEMPLATE = f"{_AGENT_BASE_PATH}/info/{{resource_id}}.json"
_PRODUCT_PATH_TEMPLATE = f"{_AGENT_BASE_PATH}/products/{{resource_id}}.json"

_INFORMATION_DATA: dict[str, dict[str, Any]] = {
    "basic-info": {
        "type": "Information",
        "title": "Test Agent Overview",
        "summary": "Demonstrates an ANP-compatible agent with sample payloads.",
        "owner": {
            "name": settings.agent_domain,
            "contact": "support@agent-connect.ai",
        },
        "capabilities": [
            "echo",
            "status-report",
            "openrpc-discovery",
        ],
        "lastUpdated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
}

_PRODUCT_DATA: dict[str, dict[str, Any]] = {
    "test-product": {
        "type": "Product",
        "name": "Synthetic Insights Bundle",
        "sku": "TEST-PROD-001",
        "description": "Provides synthetic analytics and regression-safe datasets.",
        "lifecycle": {
            "stage": "beta",
            "since": "2024-01-01",
        },
        "pricing": {
            "currency": "USD",
            "model": "subscription",
            "amount": 49.0,
            "billingPeriod": "monthly",
        },
        "support": {
            "email": "support@agent-connect.ai",
            "documentation": "https://docs.agent-connect.ai/test-agent",
        },
    }
}


def _current_timestamp() -> str:
    """Return a UTC timestamp formatted according to ISO 8601 with trailing Z."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_agent_description() -> dict[str, Any]:
    """Assemble the ANP AgentDescription payload with embedded test resources."""
    external_interface_url = f"https://{AGENT_DESCRIPTION_JSON_DOMAIN}{_EXTERNAL_INTERFACE_PATH}"

    description = {
        "protocolType": "ANP",
        "protocolVersion": "1.0.0",
        "type": "AgentDescription",
        "url": get_agent_url(f"{AGENT_PATH_PREFIX}/ad.json"),
        "name": "测试智能体",
        "did": get_agent_did("test-agent"),
        "owner": {
            "type": "Organization",
            "name": settings.agent_domain,
            "url": f"https://{settings.agent_domain}",
        },
        "description": (
            "Synthetic ANP agent used for integration testing, offering sample "
            "interfaces and structured payloads."
        ),
        "created": _current_timestamp(),
        "securityDefinitions": {
            "didwba_sc": {
                "scheme": "didwba",
                "in": "header",
                "name": "Authorization",
            }
        },
        "security": "didwba_sc",
        "information": [
            {
                "type": payload["type"],
                "description": payload["summary"],
                "url": get_agent_url(_INFO_PATH_TEMPLATE.format(resource_id=resource_id)),
            }
            for resource_id, payload in _INFORMATION_DATA.items()
        ],
        "products": [
            {
                "type": payload["type"],
                "description": payload["description"],
                "url": get_agent_url(_PRODUCT_PATH_TEMPLATE.format(resource_id=resource_id)),
            }
            for resource_id, payload in _PRODUCT_DATA.items()
        ],
        "interfaces": [
            {
                "type": "StructuredInterface",
                "protocol": "openrpc",
                "version": "1.3.2",
                "url": external_interface_url,
                "description": "External OpenRPC contract for remote procedure access.",
            },
            {
                "type": "StructuredInterface",
                "protocol": "openrpc",
                "version": "1.3.2",
                "description": "Inline OpenRPC contract with minimal demo methods.",
                "content": {
                    "openrpc": "1.3.2",
                    "info": {
                        "title": "Test Agent Inline API",
                        "version": "1.0.0",
                        "description": "Inline interface exposing echo and status utilities.",
                        "x-anp-protocol-type": "ANP",
                        "x-anp-protocol-version": "1.0.0",
                    },
                    "security": [
                        {
                            "didwba": []
                        }
                    ],
                    "servers": [
                        {
                            "name": "Test Server",
                            "url": get_agent_url("/agents/test/jsonrpc"),
                            "description": "Demo JSON-RPC endpoint exposed by the agent.",
                        }
                    ],
                    "methods": [
                        {
                            "name": "echo",
                            "summary": "Echo a provided message.",
                            "description": "Returns the supplied message to verify connectivity.",
                            "params": [
                                {
                                    "name": "message",
                                    "description": "Input message to echo back.",
                                    "required": True,
                                    "schema": {
                                        "type": "string",
                                        "minLength": 1,
                                        "maxLength": 1000,
                                        "description": "Message content that will be echoed.",
                                    },
                                }
                            ],
                            "result": {
                                "name": "echoResult",
                                "description": "Echo response payload.",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "originalMessage": {
                                            "type": "string",
                                            "description": "Original input message.",
                                        },
                                        "response": {
                                            "type": "string",
                                            "description": "Echoed response content.",
                                        },
                                        "timestamp": {
                                            "type": "string",
                                            "format": "date-time",
                                            "description": "UTC timestamp of the response.",
                                        },
                                    },
                                },
                            },
                        },
                        {
                            "name": "getStatus",
                            "summary": "Report the agent status.",
                            "description": "Returns runtime status metrics for monitoring pipelines.",
                            "params": [],
                            "result": {
                                "name": "statusResult",
                                "description": "Agent status payload.",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {
                                            "type": "string",
                                            "enum": ["online", "offline", "maintenance"],
                                            "description": "Current service availability.",
                                        },
                                        "version": {
                                            "type": "string",
                                            "description": "Deployed agent version.",
                                        },
                                        "uptime": {
                                            "type": "integer",
                                            "description": "Uptime in seconds since last restart.",
                                        },
                                        "capabilities": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            },
                                            "description": "Supported capability identifiers.",
                                        },
                                    },
                                },
                            },
                        },
                    ],
                    "components": {
                        "securitySchemes": {
                            "didwba": {
                                "type": "http",
                                "scheme": "bearer",
                                "bearerFormat": "DID-WBA",
                                "description": "DID-WBA security scheme for inter-agent auth.",
                            }
                        }
                    },
                },
            },
        ],
    }

    logger.debug("Assembled agent description payload: %s", description)
    return description


@router.get("/test/ad.json")
async def get_test_agent_description() -> JSONResponse:
    """Return the ANP agent description metadata used by integration tests."""
    try:
        agent_description = _build_agent_description()
        logger.info("Served agent description payload")
        return JSONResponse(content=agent_description)
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.exception("Failed to build agent description payload")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "message": str(exc)},
        )


@router.get("/test/info/{resource_id}.json")
async def get_agent_information(resource_id: str) -> JSONResponse:
    """Return structured information resources referenced by the agent metadata."""
    payload = _INFORMATION_DATA.get(resource_id)
    if payload is None:
        logger.warning("Information resource not found: %s", resource_id)
        raise HTTPException(status_code=404, detail="Information resource not found")

    logger.info("Served information resource: %s", resource_id)
    return JSONResponse(content=payload)


@router.get("/test/products/{resource_id}.json")
async def get_agent_product(resource_id: str) -> JSONResponse:
    """Return product metadata linked within the agent description document."""
    payload = _PRODUCT_DATA.get(resource_id)
    if payload is None:
        logger.warning("Product resource not found: %s", resource_id)
        raise HTTPException(status_code=404, detail="Product resource not found")

    logger.info("Served product resource: %s", resource_id)
    return JSONResponse(content=payload)


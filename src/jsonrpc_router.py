"""JSON-RPC Router for ANP Agent OpenRPC interfaces.

This module implements the JSON-RPC endpoints for both inline and external
OpenRPC interfaces defined in the agent description.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents")

# Start time for uptime calculation
_start_time = time.time()


def _create_error_response(request_id: Optional[Any], code: int, message: str, data: Optional[Any] = None) -> Dict[str, Any]:
    """Create a JSON-RPC error response."""
    return {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message,
            "data": data
        },
        "id": request_id
    }


def _create_success_response(request_id: Optional[Any], result: Any) -> Dict[str, Any]:
    """Create a JSON-RPC success response."""
    return {
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id
    }


def _current_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Inline OpenRPC Interface Methods (echo, getStatus)

def _handle_echo(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle the echo method from inline interface."""
    if not params or "message" not in params:
        raise ValueError("Missing required parameter: message")

    message = params["message"]
    if not isinstance(message, str):
        raise ValueError("Parameter 'message' must be a string")

    if len(message) < 1 or len(message) > 1000:
        raise ValueError("Message length must be between 1 and 1000 characters")

    return {
        "originalMessage": message,
        "response": f"Echo: {message}",
        "timestamp": _current_timestamp()
    }


def _handle_get_status(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle the getStatus method from inline interface."""
    uptime_seconds = int(time.time() - _start_time)

    return {
        "status": "online",
        "version": "1.0.0",
        "uptime": uptime_seconds,
        "capabilities": ["echo", "status-report", "add", "greet"]
    }


# Simplified External Interface Methods (add, greet)

def _handle_add(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle the add method from external interface."""
    if not params or "a" not in params or "b" not in params:
        raise ValueError("Missing required parameters: a and b")

    a = params["a"]
    b = params["b"]

    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError("Parameters a and b must be numbers")

    result = a + b
    return {"result": result}


def _handle_greet(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle the greet method from external interface."""
    if not params or "name" not in params:
        raise ValueError("Missing required parameter: name")

    name = params["name"]
    if not isinstance(name, str):
        raise ValueError("Parameter 'name' must be a string")

    if len(name.strip()) == 0:
        raise ValueError("Name cannot be empty")

    message = f"你好, {name}! 欢迎使用ANP智能体!"
    return {"message": message}


# Route handlers

@router.post("/test/jsonrpc")
async def handle_unified_jsonrpc(request: Request) -> JSONResponse:
    """Handle JSON-RPC requests for all methods (echo, getStatus, add, greet)."""
    try:
        # Parse request body
        body = await request.json()

        # Validate JSON-RPC request format
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                content=_create_error_response(
                    body.get("id"), -32600, "Invalid Request", "JSON-RPC version must be 2.0"
                )
            )

        method = body.get("method")
        params = body.get("params")
        request_id = body.get("id")

        if not method:
            return JSONResponse(
                content=_create_error_response(request_id, -32600, "Invalid Request", "Missing method")
            )

        # Route to appropriate method handler
        try:
            if method == "echo":
                result = _handle_echo(params)
            elif method == "getStatus":
                result = _handle_get_status(params)
            elif method == "add":
                result = _handle_add(params)
            elif method == "greet":
                result = _handle_greet(params)
            else:
                return JSONResponse(
                    content=_create_error_response(request_id, -32601, "Method not found", f"Method '{method}' not found")
                )

            logger.info(f"Successfully handled method: {method}")
            return JSONResponse(content=_create_success_response(request_id, result))

        except ValueError as e:
            logger.warning(f"Invalid parameters for method {method}: {str(e)}")
            return JSONResponse(
                content=_create_error_response(request_id, -32602, "Invalid params", str(e))
            )
        except Exception as e:
            logger.error(f"Internal error handling method {method}: {str(e)}")
            return JSONResponse(
                content=_create_error_response(request_id, -32603, "Internal error", str(e))
            )

    except Exception as e:
        logger.error(f"Error parsing JSON-RPC request: {str(e)}")
        return JSONResponse(
            content=_create_error_response(None, -32700, "Parse error", "Invalid JSON")
        )
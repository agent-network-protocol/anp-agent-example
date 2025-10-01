"""JSON-RPC Router for ANP Agent OpenRPC interfaces.

This module implements the JSON-RPC endpoints for both inline and external
OpenRPC interfaces defined in the agent description.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Start time for uptime calculation
_start_time = time.time()


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request model."""
    jsonrpc: str = Field(..., description="JSON-RPC version")
    method: str = Field(..., description="Method name")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Method parameters")
    id: Optional[Any] = Field(default=None, description="Request ID")


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response model."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error model."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: Optional[Any] = Field(default=None, description="Additional error data")


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
        "capabilities": ["echo", "status-report", "openrpc-discovery"]
    }


# External OpenRPC Interface Methods (calculateSum, validateData, generateReport)

def _handle_calculate_sum(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle the calculateSum method from external interface."""
    if not params or "numbers" not in params:
        raise ValueError("Missing required parameter: numbers")

    numbers = params["numbers"]
    if not isinstance(numbers, list):
        raise ValueError("Parameter 'numbers' must be an array")

    if len(numbers) < 1 or len(numbers) > 100:
        raise ValueError("Array length must be between 1 and 100")

    # Validate all items are numbers
    for i, num in enumerate(numbers):
        if not isinstance(num, (int, float)):
            raise ValueError(f"All array items must be numbers, item at index {i} is not a number")

    total = sum(numbers)
    count = len(numbers)
    average = total / count if count > 0 else 0

    return {
        "sum": total,
        "count": count,
        "average": average
    }


def _handle_validate_data(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle the validateData method from external interface."""
    if not params or "data" not in params:
        raise ValueError("Missing required parameter: data")

    data = params["data"]
    if not isinstance(data, dict):
        raise ValueError("Parameter 'data' must be an object")

    issues = []

    # Validate email
    if "email" in data:
        email = data["email"]
        if not isinstance(email, str) or "@" not in email:
            issues.append({"field": "email", "message": "Invalid email format"})

    # Validate phone
    if "phone" in data:
        phone = data["phone"]
        if not isinstance(phone, str) or not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            issues.append({"field": "phone", "message": "Invalid phone number format"})

    # Validate age
    if "age" in data:
        age = data["age"]
        if not isinstance(age, int) or age < 0 or age > 150:
            issues.append({"field": "age", "message": "Age must be between 0 and 150"})

    # Validate name
    if "name" in data:
        name = data["name"]
        if not isinstance(name, str) or len(name) < 1 or len(name) > 100:
            issues.append({"field": "name", "message": "Name must be between 1 and 100 characters"})

    return {
        "isValid": len(issues) == 0,
        "issues": issues,
        "timestamp": _current_timestamp()
    }


def _handle_generate_report(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle the generateReport method from external interface."""
    if not params or "reportRequest" not in params:
        raise ValueError("Missing required parameter: reportRequest")

    report_request = params["reportRequest"]
    if not isinstance(report_request, dict):
        raise ValueError("Parameter 'reportRequest' must be an object")

    # Validate required fields
    if "title" not in report_request or "content" not in report_request:
        raise ValueError("Missing required fields: title and content")

    title = report_request["title"]
    content = report_request["content"]

    if not isinstance(title, str) or len(title) < 3 or len(title) > 120:
        raise ValueError("Title must be between 3 and 120 characters")

    if not isinstance(content, str):
        raise ValueError("Content must be a string")

    # Get format parameter (optional)
    format_type = params.get("format", "json")
    if format_type not in ["json", "html", "pdf", "markdown"]:
        format_type = "json"

    # Generate report ID
    report_id = str(uuid.uuid4())

    # Format content based on requested format
    if format_type == "json":
        formatted_content = {
            "title": title,
            "content": content,
            "metadata": report_request.get("metadata", {}),
            "attachments": report_request.get("attachments", [])
        }
        formatted_content = str(formatted_content)
    elif format_type == "html":
        formatted_content = f"<html><head><title>{title}</title></head><body><h1>{title}</h1><p>{content}</p></body></html>"
    elif format_type == "markdown":
        formatted_content = f"# {title}\n\n{content}"
    elif format_type == "pdf":
        formatted_content = f"PDF: {title}\n{content}"
    else:
        formatted_content = content

    return {
        "reportId": report_id,
        "content": formatted_content,
        "format": format_type,
        "generatedAt": _current_timestamp(),
        "size": len(formatted_content)
    }


# Route handlers

@router.post("/test/jsonrpc")
async def handle_inline_jsonrpc(request: Request) -> JSONResponse:
    """Handle JSON-RPC requests for inline OpenRPC interface (echo, getStatus)."""
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


@router.post("/external/jsonrpc")
async def handle_external_jsonrpc(request: Request) -> JSONResponse:
    """Handle JSON-RPC requests for external OpenRPC interface (calculateSum, validateData, generateReport)."""
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
            if method == "calculateSum":
                result = _handle_calculate_sum(params)
            elif method == "validateData":
                result = _handle_validate_data(params)
            elif method == "generateReport":
                result = _handle_generate_report(params)
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
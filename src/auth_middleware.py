"""
Authentication middleware for FastAPI using the DidWbaVerifier SDK.

This module stays in the application layer (business layer) and wires framework
objects (FastAPI Request/Response) to the SDK that is framework-agnostic.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

# Import DID-WBA verifier from agent-connect library
from agent_connect.authentication.did_wba_verifier import (
    DidWbaVerifier,
    DidWbaVerifierConfig,
    DidWbaVerifierError,
)
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

# Import config from local config module
import config

logger = logging.getLogger(__name__)

# Define exempt paths that don't require authentication
EXEMPT_PATHS = [
    "/favicon.ico",
    "/v1/status",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/wba/user/",  # Allow access to DID documents
    "/",  # Allow access to root endpoint
    "/v1/chat",
    "/static/",  # Allow access to all paths under /static/
    "/agents/test/ad.json",  # Allow access to agent description for testing
    # "/agents/test/api/",  # Allow access to API files for testing
    # "/agents/test/jsonrpc",  # Allow access to unified JSON-RPC interface for testing
]


def _read_text_file(path: str | None) -> str | None:
    """Read a text file, returning its content or None when not available."""
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as exc:
        logger.error("Failed to read file %s: %s", path, exc)
        return None


# Initialize verifier singleton with application configuration
_verifier = DidWbaVerifier(
    DidWbaVerifierConfig(
        jwt_private_key=_read_text_file(config.JWT_PRIVATE_KEY_PATH),
        jwt_public_key=_read_text_file(config.JWT_PUBLIC_KEY_PATH),
        jwt_algorithm=config.JWT_ALGORITHM,
        access_token_expire_minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES,
        nonce_expiration_minutes=config.AUTH_NONCE_EXPIRY_MINUTES,
        timestamp_expiration_minutes=config.AUTH_TIMESTAMP_EXPIRY_MINUTES,
    )
)


def _get_and_validate_domain(request: Request) -> str:
    """Extract the domain from the Host header."""
    host = request.headers.get("host", "")
    domain = host.split(":")[0]
    return domain


async def verify_auth_header(request: Request) -> dict:
    """Verify authentication header and return authenticated user data.

    Raises HTTPException if authentication fails.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    domain = _get_and_validate_domain(request)
    try:
        return await _verifier.verify_auth_header(auth_header, domain)
    except DidWbaVerifierError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


async def authenticate_request(request: Request) -> dict | None:
    """Authenticate a request and return user data if successful.

    Returns None for exempt paths.
    """
    logger.info("Authenticating request to path: %s", request.url.path)
    logger.info("Request headers: %s", request.headers)

    for exempt_path in EXEMPT_PATHS:
        # Root path exact match only
        if exempt_path == "/":
            if request.url.path == "/":
                logger.info(
                    "Path %s is exempt from authentication (matched root path)",
                    request.url.path,
                )
                return None
        elif request.url.path == exempt_path or (
            exempt_path.endswith("/") and request.url.path.startswith(exempt_path)
        ) or (
            not exempt_path.endswith("/") and request.url.path.startswith(exempt_path + "/")
        ):
            logger.info(
                "Path %s is exempt from authentication (matched %s)",
                request.url.path,
                exempt_path,
            )
            return None

    logger.info("Path %s requires authentication", request.url.path)
    return await verify_auth_header(request)


async def auth_middleware(request: Request, call_next: Callable) -> Response:
    """Authentication middleware for FastAPI."""
    try:
        response_auth = await authenticate_request(request)
        headers = dict(request.headers)
        request.state.headers = headers
        logger.info("Authenticated request headers stored in request.state")
        logger.info("Authenticated Response auth: %s", response_auth)

        if response_auth is not None:
            response = await call_next(request)
            if response_auth.get("token_type", " ") == "bearer":
                response.headers["authorization"] = (
                    "bearer " + response_auth["access_token"]
                )
                return response
            else:
                response.headers["authorization"] = headers.get("authorization", "")
                return response
        else:
            logger.info("Authentication skipped for exempt path")
            return await call_next(request)

    except HTTPException as exc:
        logger.error("Authentication error: %s", exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    except Exception as exc:
        logger.error("Unexpected error in auth middleware: %s", exc)
        # 在测试环境中，将不支持的认证格式转换为401而不是500
        error_msg = str(exc).lower()
        if any(keyword in error_msg for keyword in ["authorization", "bearer", "didwba", "token", "format"]):
            return JSONResponse(
                status_code=401, content={"detail": f"Authentication error: {str(exc)}"}
            )
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

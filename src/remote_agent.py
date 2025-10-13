#!/usr/bin/env python3
"""
ANP Remote Agent Example.

This example demonstrates a complete FastANP remote agent with:
- Multiple Information documents (static and dynamic)
- Complex data models using Pydantic
- Multiple interface methods
- Context injection for session management
- Custom ad.json route
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from anp.authentication.did_wba_verifier import DidWbaVerifierConfig
from anp.fastanp import Context, FastANP
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import load_public_did

_project_root = Path(__file__).parent.parent

HOST = "0.0.0.0"
PORT = "8000"
AGENT_DESCRIPTION_JSON_DOMAIN=f"{HOST}:{PORT}"
LOG_LEVEL = "INFO"

# did document path
PUBLIC_DID_DOCUMENT_PATH = _project_root / "docs" / "did_public" / "public-did-doc.json"

# jwt private key path
JWT_PRIVATE_KEY_PATH = _project_root / "docs" / "jwt_key" / "RS256-private.pem"
JWT_PUBLIC_KEY_PATH = _project_root / "docs" / "jwt_key" / "RS256-public.pem"

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ANP Remote Agent",
    description="Remote ANP protocol agent providing test interfaces and services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load JWT keys for authentication
with open(JWT_PRIVATE_KEY_PATH, encoding="utf-8") as handle:
    jwt_private_key = handle.read()
with open(JWT_PUBLIC_KEY_PATH, encoding="utf-8") as handle:
    jwt_public_key = handle.read()

# Create auth config
auth_config = DidWbaVerifierConfig(
    jwt_private_key=jwt_private_key,
    jwt_public_key=jwt_public_key,
    jwt_algorithm="RS256",
    allowed_domains=["localhost", "0.0.0.0", "127.0.0.1", AGENT_DESCRIPTION_JSON_DOMAIN]
)

# Initialize FastANP plugin
anp = FastANP(
    app=app,
    name="Remote Test Agent",
    description="Remote ANP agent for testing agent-to-agent communication",
    base_url="http://localhost:8000",
    did=load_public_did(PUBLIC_DID_DOCUMENT_PATH),
    owner={
        "type": "Organization",
        "name": AGENT_DESCRIPTION_JSON_DOMAIN,
        "url": "http://localhost:8000",
    },
    jsonrpc_server_url="/agents/remote/jsonrpc",
    jsonrpc_server_name="Remote Agent JSON-RPC API",
    jsonrpc_server_description="Remote Agent JSON-RPC API for ANP protocol",
    enable_auth_middleware=False,  # Disable auth for demo
    auth_config=auth_config
)

# Start time for uptime calculation
_start_time = time.time()

# Optional: Add authentication middleware
if anp.auth_middleware:
    app.add_middleware(anp.auth_middleware)


# Define data models
class EchoParams(BaseModel):
    """Echo method parameters."""
    message: str


class GreetParams(BaseModel):
    """Greet method parameters."""
    name: str


# Custom ad.json route
@app.get("/agents/remote/ad.json", tags=["agent"])
def get_agent_description():
    """
    Get Agent Description for the remote agent.
    """
    # 1. Get common header from FastANP
    ad = anp.get_common_header()

    # 2. Add Information items (user-defined)
    ad["information"] = [
        {
            "type": "Information",
            "description": "Remote ANP agent for testing agent-to-agent communication",
            "url": get_agent_url("/agents/remote/info/basic-info.json")
        }
    ]

    # 3. Add Interface items using FastANP helpers
    ad["interfaces"] = [
        anp.interfaces[echo].content,
        anp.interfaces[greet].link_summary,
    ]

    return ad


# Register interface methods

@anp.interface("/agents/remote/api/echo.json", description="Echo a provided message")
def echo(params: EchoParams) -> dict:
    """
    Echo a provided message.

    Args:
        params: Echo parameters containing the message

    Returns:
        Dictionary with echo response
    """
    return {
        "originalMessage": params.message,
        "response": f"Echo from remote: {params.message}",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


@anp.interface("/agents/remote/api/greet.json", description="Generate personalized greeting")
def greet(params: GreetParams, ctx: Context) -> dict:
    """
    Generate personalized greeting with session context.

    Context is automatically injected by FastANP based on DID + Access Token.

    Args:
        params: Greet parameters containing the name
        ctx: Automatically injected context (contains session, DID, request info)

    Returns:
        Dictionary with greeting message and session information
    """
    # Access session data
    session_id = ctx.session.id
    did = ctx.did

    # Store/retrieve session data
    visit_count = ctx.session.get("visit_count", 0)
    visit_count += 1
    ctx.session.set("visit_count", visit_count)

    message = f"Hello, {params.name}! Welcome to Remote ANP Agent!"

    return {
        "message": message,
        "session_id": session_id,
        "did": did,
        "visit_count": visit_count,
        "agent": "remote"
    }


# Additional static routes (user-defined)

@app.get("/agents/remote/info/basic-info.json", tags=["information"])
def get_basic_info():
    """Get basic agent information."""
    return {
        "type": "Information",
        "title": "Remote Agent Overview",
        "summary": "Remote ANP agent for testing agent-to-agent communication",
        "owner": {
            "name": AGENT_DESCRIPTION_JSON_DOMAIN,
            "contact": "support@agent-connect.ai",
        },
        "capabilities": [
            "echo",
            "greet",
        ],
        "lastUpdated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def get_agent_url(path: str) -> str:
    """
    Generate the full URL for agent resources.

    Args:
        path: Resource path beginning with a slash.

    Returns:
        Fully qualified URL string.
    """
    import ipaddress

    domain = AGENT_DESCRIPTION_JSON_DOMAIN
    host = domain

    if ":" in domain:
        if domain.startswith("["):
            bracket_end = domain.find("]")
            if bracket_end != -1:
                host = domain[1:bracket_end]
        else:
            host = domain.rsplit(":", 1)[0]

    if host in ("localhost", "127.0.0.1", "::1"):
        protocol = "http"
    else:
        try:
            ipaddress.ip_address(host)
            protocol = "http"
        except ValueError:
            protocol = "https"

    return f"{protocol}://{domain}{path}"

def main():
    """Run the ANP remote agent server."""
    import uvicorn

    logger.info("Starting ANP Remote Agent Service...")
    logger.info(f"- Agent Description: http://{HOST}:{PORT}/agents/remote/ad.json")
    logger.info(f"- JSON-RPC endpoint: http://{HOST}:{PORT}/agents/remote/jsonrpc")
    logger.info(f"- Health check: http://{HOST}:{PORT}/health")
    logger.info(f"- API Docs: http://{HOST}:{PORT}/docs")

    uvicorn.run(
        "remote_agent:app",
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()

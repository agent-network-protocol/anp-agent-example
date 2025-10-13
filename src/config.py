"""
OpenAI configuration helpers.

This module centralizes environment-driven OpenAI settings so that local tools
share consistent defaults.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent
_env_file = _project_root / ".env"

if _env_file.exists():
    load_dotenv(_env_file)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
DEFAULT_OPENAI_MODEL = os.getenv("DEFAULT_OPENAI_MODEL")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
AGENT_DESCRIPTION_JSON_DOMAIN = os.getenv("AGENT_DESCRIPTION_JSON_DOMAIN", f"{HOST}:{PORT}")


class OpenAISettings:
    """Container for OpenAI-related configuration values."""

    def __init__(self) -> None:
        self.api_key = OPENAI_API_KEY
        self.base_url = OPENAI_BASE_URL
        self.default_model = DEFAULT_OPENAI_MODEL

    def validate(self) -> list[str]:
        """Return validation errors for missing critical OpenAI settings."""
        errors: list[str] = []
        if not self.api_key:
            errors.append("OPENAI_API_KEY is required for OpenAI access.")
        return errors


class ServerSettings:
    """Container for server configuration values."""

    def __init__(self) -> None:
        self.host = HOST
        self.port = PORT
        self.agent_description_json_domain = AGENT_DESCRIPTION_JSON_DOMAIN

    def get_agent_url(self, path: str = "") -> str:
        """
        Generate the full URL for agent resources.

        Args:
            path: Resource path beginning with a slash.

        Returns:
            Fully qualified URL string.
        """
        return get_agent_url(self.agent_description_json_domain, path)


def load_public_did(document_path: Path) -> str:
    """
    Load remote agent DID from the public DID document.

    Args:
        document_path: Path to the DID document file.

    Returns:
        DID identifier string.

    Raises:
        RuntimeError: If the document cannot be read or the DID is missing.
    """
    try:
        with document_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise RuntimeError(f"DID document not found at {document_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DID document at {document_path} is not valid JSON") from exc

    did = data.get("id")
    if not isinstance(did, str) or not did.strip():
        raise RuntimeError(f"DID document at {document_path} is missing a valid 'id' field")

    return did.strip()


def get_agent_url(ad_domain: str, path: str) -> str:
    """
    Generate the full URL for agent resources.

    Args:
        path: Resource path beginning with a slash.

    Returns:
        Fully qualified URL string.
    """
    import ipaddress

    domain = ad_domain
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

settings = OpenAISettings()
server_settings = ServerSettings()

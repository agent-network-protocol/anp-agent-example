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


settings = OpenAISettings()

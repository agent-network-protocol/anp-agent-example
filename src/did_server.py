"""DID Server implementation for creating and managing DID-WBA documents.

This module provides a FastAPI-based DID server that:
1. Creates DID documents and manages cryptographic keys
2. Stores private keys securely (should be stored in /etc/appname/keys/ with root-only access)
3. Stores public keys in accessible locations or database
4. Provides HTTP GET endpoint to retrieve DID documents via DID-to-URL resolution
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from anp.authentication import create_did_wba_document
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DIDConfig(BaseModel):
    """Configuration for DID document creation."""

    hostname: str = Field(..., description="Hostname for the DID identifier")
    path_segments: list[str] = Field(
        default_factory=list,
        description="Path segments for the DID identifier",
    )
    agent_description_url: str = Field(
        ...,
        description="URL to the agent description",
    )
    private_key_dir: str = Field(
        default="/etc/appname/keys",
        description="Directory for storing private keys (should be root-only access)",
    )
    public_key_dir: str = Field(
        default="./keys/public",
        description="Directory for storing public keys",
    )
    did_document_path: str = Field(
        default="./did_documents",
        description="Directory for storing DID documents",
    )


class DIDKeyManager:
    """Manages DID document creation and cryptographic key storage."""

    def __init__(self, config: DIDConfig) -> None:
        """Initialize the DID key manager.

        Args:
            config: Configuration for DID document creation.
        """
        self.config = config
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        # NOTE: In production, /etc/appname/keys should be created with:
        # - Owner: root or service user
        # - Permissions: 0700 (drwx------)
        # - Only root and the service user should have read access
        for directory in [
            self.config.private_key_dir,
            self.config.public_key_dir,
            self.config.did_document_path,
        ]:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")

    def create_did_document(self) -> dict[str, Any]:
        """Create a DID-WBA document and store associated keys.

        Returns:
            The created DID document as a dictionary.

        Raises:
            RuntimeError: If document creation fails.
        """
        try:
            # Create DID document using ANP library
            did_document, keys = create_did_wba_document(
                hostname=self.config.hostname,
                path_segments=self.config.path_segments,
                agent_description_url=self.config.agent_description_url,
            )

            did_identifier = did_document["id"]
            logger.info(f"Created DID document with identifier: {did_identifier}")

            # Log the corresponding URL for this DID
            url_path = "/".join(self.config.path_segments)
            logger.info(f"DID document will be accessible at: https://{self.config.hostname}/{url_path}/did.json")

            # Save DID document
            self._save_did_document(did_document)

            # Save keys
            self._save_keys(keys)

            return did_document

        except Exception as exc:
            logger.error(f"Failed to create DID document: {exc}")
            raise RuntimeError(f"DID document creation failed: {exc}") from exc

    def _save_did_document(self, did_document: dict[str, Any]) -> None:
        """Save the DID document to disk.

        Args:
            did_document: The DID document to save.
        """
        did_identifier = did_document["id"]
        # Use DID as filename (replace colons with underscores for filesystem safety)
        safe_filename = did_identifier.replace(":", "_").replace("/", "_")
        did_path = Path(self.config.did_document_path) / f"{safe_filename}.json"

        did_path.write_text(
            json.dumps(did_document, indent=2),
            encoding="utf-8",
        )
        logger.info(f"DID document saved to: {did_path}")

    def _save_keys(self, keys: dict[str, tuple[bytes, bytes]]) -> None:
        """Save cryptographic keys to appropriate directories.

        Private keys are saved to a secure directory (should be /etc/appname/keys/).
        Public keys are saved to a publicly accessible directory.

        Args:
            keys: Dictionary mapping key fragments to (private_bytes, public_bytes).
        """
        for fragment, (private_bytes, public_bytes) in keys.items():
            # Save private key to secure directory
            # WARNING: In production, ensure /etc/appname/keys has proper permissions:
            # - chmod 700 /etc/appname/keys
            # - chown root:root /etc/appname/keys (or service_user:service_user)
            private_path = Path(self.config.private_key_dir) / f"{fragment}_private.pem"
            private_path.write_bytes(private_bytes)
            # Set restrictive permissions on private key file
            os.chmod(private_path, 0o600)  # rw-------
            logger.info(
                f"Private key saved: {private_path} (permissions: 0600)"
            )

            # Save public key to accessible directory
            public_path = Path(self.config.public_key_dir) / f"{fragment}_public.pem"
            public_path.write_bytes(public_bytes)
            logger.info(f"Public key saved: {public_path}")

    def get_did_document(self, did_identifier: str) -> dict[str, Any]:
        """Retrieve a DID document by its identifier.

        Args:
            did_identifier: The DID identifier.

        Returns:
            The DID document as a dictionary.

        Raises:
            FileNotFoundError: If the DID document is not found.
            json.JSONDecodeError: If the document is not valid JSON.
        """
        safe_filename = did_identifier.replace(":", "_").replace("/", "_")
        did_path = Path(self.config.did_document_path) / f"{safe_filename}.json"

        if not did_path.exists():
            raise FileNotFoundError(f"DID document not found: {did_identifier}")

        with did_path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def get_public_key(self, fragment: str) -> bytes:
        """Retrieve a public key by its fragment identifier.

        Args:
            fragment: The key fragment identifier.

        Returns:
            The public key bytes.

        Raises:
            FileNotFoundError: If the public key is not found.
        """
        public_path = Path(self.config.public_key_dir) / f"{fragment}_public.pem"

        if not public_path.exists():
            raise FileNotFoundError(f"Public key not found: {fragment}")

        return public_path.read_bytes()


class DIDServer:
    """FastAPI server for DID document resolution."""

    def __init__(self, key_manager: DIDKeyManager) -> None:
        """Initialize the DID server.

        Args:
            key_manager: The DID key manager instance.
        """
        self.key_manager = key_manager
        self.app = FastAPI(
            title="DID Server",
            description="DID-WBA document resolution server",
            version="1.0.0",
        )
        self._register_routes()

    def _register_routes(self) -> None:
        """Register FastAPI routes."""

        @self.app.get("/{path:path}/did.json")
        async def resolve_did(path: str) -> dict[str, Any]:
            """Resolve a DID to its DID document via HTTP GET.

            This endpoint implements DID-to-URL resolution according to the
            DID-WBA specification. The URL path is converted to a DID identifier.

            Args:
                path: The URL path (everything before /did.json).

            Returns:
                The DID document as JSON.

            Raises:
                HTTPException: If the DID document is not found.
            """
            # Convert URL path to DID identifier according to DID-WBA spec
            # Example: /user/alice -> did:wba:example.com:user:alice
            # The hostname is taken from the server configuration
            path_segments = path.strip("/").split("/")

            # Construct DID identifier: did:wba:{hostname}:{path_segments}
            did_identifier = f"did:wba:{self.key_manager.config.hostname}:{':'.join(path_segments)}"

            logger.info(f"Resolving DID: {did_identifier} from URL path: /{path}/did.json")

            try:
                did_document = self.key_manager.get_did_document(did_identifier)
                return did_document
            except FileNotFoundError as exc:
                logger.warning(f"DID not found: {did_identifier}")
                raise HTTPException(
                    status_code=404,
                    detail=f"DID document not found: {did_identifier}",
                ) from exc
            except json.JSONDecodeError as exc:
                logger.error(f"Invalid DID document format: {did_identifier}")
                raise HTTPException(
                    status_code=500,
                    detail="Invalid DID document format",
                ) from exc



def create_did_server(config: DIDConfig) -> DIDServer:
    """Factory function to create a DID server instance.

    Args:
        config: Configuration for the DID server.

    Returns:
        Configured DIDServer instance.
    """
    key_manager = DIDKeyManager(config)
    return DIDServer(key_manager)


# Example usage
if __name__ == "__main__":
    import uvicorn

    # Example configuration
    config = DIDConfig(
        hostname="example.com",
        path_segments=["user", "alice"],
        agent_description_url="https://example.com/user/alice",
        # NOTE: In production, use /etc/appname/keys with proper permissions
        private_key_dir="./keys/private",  # Development only
        public_key_dir="./keys/public",
        did_document_path="./did_documents",
    )

    # Create DID server
    server = create_did_server(config)

    # Create a DID document on startup
    logger.info("Creating DID document...")
    did_doc = server.key_manager.create_did_document()
    logger.info(f"DID created: {did_doc['id']}")

    # Run the server
    uvicorn.run(server.app, host="0.0.0.0", port=8080)

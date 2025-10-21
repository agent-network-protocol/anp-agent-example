"""Unit tests for the DID server module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from src.did_server import (
    DIDConfig,
    DIDKeyManager,
    DIDServer,
    create_did_server,
)


@pytest.fixture
def temp_dirs() -> dict[str, str]:
    """Create temporary directories for testing.

    Returns:
        Dictionary with paths to temporary directories.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        private_dir = base_path / "private"
        public_dir = base_path / "public"
        did_doc_dir = base_path / "did_documents"

        private_dir.mkdir(parents=True)
        public_dir.mkdir(parents=True)
        did_doc_dir.mkdir(parents=True)

        yield {
            "private_key_dir": str(private_dir),
            "public_key_dir": str(public_dir),
            "did_document_path": str(did_doc_dir),
        }


@pytest.fixture
def did_config(temp_dirs: dict[str, str]) -> DIDConfig:
    """Create a test DID configuration.

    Args:
        temp_dirs: Temporary directories for testing.

    Returns:
        DIDConfig instance for testing.
    """
    return DIDConfig(
        hostname="test.example.com",
        path_segments=["agents", "test"],
        agent_description_url="https://test.example.com/agents/test",
        private_key_dir=temp_dirs["private_key_dir"],
        public_key_dir=temp_dirs["public_key_dir"],
        did_document_path=temp_dirs["did_document_path"],
    )


@pytest.fixture
def key_manager(did_config: DIDConfig) -> DIDKeyManager:
    """Create a DID key manager for testing.

    Args:
        did_config: DID configuration.

    Returns:
        DIDKeyManager instance.
    """
    return DIDKeyManager(did_config)


@pytest.fixture
def did_server(key_manager: DIDKeyManager) -> DIDServer:
    """Create a DID server for testing.

    Args:
        key_manager: DID key manager.

    Returns:
        DIDServer instance.
    """
    return DIDServer(key_manager)


class TestDIDKeyManager:
    """Test suite for DIDKeyManager class."""

    def test_initialization(self, did_config: DIDConfig) -> None:
        """Test that DIDKeyManager initializes correctly."""
        manager = DIDKeyManager(did_config)
        assert manager.config == did_config

        # Verify directories are created
        assert Path(did_config.private_key_dir).exists()
        assert Path(did_config.public_key_dir).exists()
        assert Path(did_config.did_document_path).exists()

    def test_create_did_document(self, key_manager: DIDKeyManager) -> None:
        """Test DID document creation."""
        did_document = key_manager.create_did_document()

        # Verify DID document structure
        assert "id" in did_document
        assert did_document["id"].startswith("did:wba:")
        assert "verificationMethod" in did_document
        assert "authentication" in did_document

        # Verify DID identifier format (ANP library uses colons for path segments)
        expected_did = "did:wba:test.example.com:agents:test"
        assert did_document["id"] == expected_did

    def test_save_did_document(
        self,
        key_manager: DIDKeyManager,
        did_config: DIDConfig,
    ) -> None:
        """Test that DID documents are saved correctly."""
        did_document = key_manager.create_did_document()
        did_identifier = did_document["id"]

        # Verify file exists
        safe_filename = did_identifier.replace(":", "_").replace("/", "_")
        did_path = Path(did_config.did_document_path) / f"{safe_filename}.json"
        assert did_path.exists()

        # Verify content
        with did_path.open(encoding="utf-8") as handle:
            saved_doc = json.load(handle)
        assert saved_doc == did_document

    def test_save_keys(
        self,
        key_manager: DIDKeyManager,
        did_config: DIDConfig,
    ) -> None:
        """Test that keys are saved to correct locations."""
        key_manager.create_did_document()

        # Verify private keys exist
        private_dir = Path(did_config.private_key_dir)
        private_keys = list(private_dir.glob("*_private.pem"))
        assert len(private_keys) > 0

        # Verify public keys exist
        public_dir = Path(did_config.public_key_dir)
        public_keys = list(public_dir.glob("*_public.pem"))
        assert len(public_keys) > 0

        # Verify same number of private and public keys
        assert len(private_keys) == len(public_keys)

    def test_get_did_document(self, key_manager: DIDKeyManager) -> None:
        """Test retrieving a DID document."""
        created_doc = key_manager.create_did_document()
        did_identifier = created_doc["id"]

        # Retrieve the document
        retrieved_doc = key_manager.get_did_document(did_identifier)
        assert retrieved_doc == created_doc

    def test_get_did_document_not_found(self, key_manager: DIDKeyManager) -> None:
        """Test that FileNotFoundError is raised for non-existent DID."""
        with pytest.raises(FileNotFoundError):
            key_manager.get_did_document("did:wba:nonexistent.com")

    def test_get_public_key(self, key_manager: DIDKeyManager) -> None:
        """Test retrieving a public key."""
        key_manager.create_did_document()

        # Find a key fragment
        public_dir = Path(key_manager.config.public_key_dir)
        public_keys = list(public_dir.glob("*_public.pem"))
        assert len(public_keys) > 0

        # Extract fragment from filename
        fragment = public_keys[0].stem.replace("_public", "")

        # Retrieve the public key
        public_key_bytes = key_manager.get_public_key(fragment)
        assert isinstance(public_key_bytes, bytes)
        assert b"BEGIN PUBLIC KEY" in public_key_bytes

    def test_get_public_key_not_found(self, key_manager: DIDKeyManager) -> None:
        """Test that FileNotFoundError is raised for non-existent key."""
        with pytest.raises(FileNotFoundError):
            key_manager.get_public_key("nonexistent_fragment")


class TestDIDServer:
    """Test suite for DIDServer class."""

    def test_initialization(self, did_server: DIDServer) -> None:
        """Test that DIDServer initializes correctly."""
        assert did_server.app is not None
        assert did_server.key_manager is not None

    @pytest.mark.asyncio
    async def test_health_check(self, did_server: DIDServer) -> None:
        """Test the health check endpoint."""
        transport = ASGITransport(app=did_server.app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_resolve_did(self, did_server: DIDServer) -> None:
        """Test DID resolution endpoint."""
        # Create a DID document
        did_document = did_server.key_manager.create_did_document()
        did_identifier = did_document["id"]

        # Convert DID to URL path
        # did:wba:test.example.com/agents/test -> /did/wba/test.example.com/agents/test
        did_path = did_identifier.replace("did:", "")

        transport = ASGITransport(app=did_server.app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get(f"/did/{did_path}")
            assert response.status_code == 200

            resolved_doc = response.json()
            assert resolved_doc["id"] == did_identifier
            assert "verificationMethod" in resolved_doc

    @pytest.mark.asyncio
    async def test_resolve_did_not_found(self, did_server: DIDServer) -> None:
        """Test DID resolution with non-existent DID."""
        transport = ASGITransport(app=did_server.app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get("/did/wba/nonexistent.com")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_public_key_endpoint(self, did_server: DIDServer) -> None:
        """Test public key retrieval endpoint."""
        # Create a DID document
        did_server.key_manager.create_did_document()

        # Find a key fragment
        public_dir = Path(did_server.key_manager.config.public_key_dir)
        public_keys = list(public_dir.glob("*_public.pem"))
        assert len(public_keys) > 0

        fragment = public_keys[0].stem.replace("_public", "")

        transport = ASGITransport(app=did_server.app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get(f"/keys/public/{fragment}")
            assert response.status_code == 200

            data = response.json()
            assert data["fragment"] == fragment
            assert "BEGIN PUBLIC KEY" in data["public_key"]

    @pytest.mark.asyncio
    async def test_get_public_key_not_found(self, did_server: DIDServer) -> None:
        """Test public key endpoint with non-existent key."""
        transport = ASGITransport(app=did_server.app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get("/keys/public/nonexistent")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestCreateDIDServer:
    """Test suite for create_did_server factory function."""

    def test_create_did_server(self, did_config: DIDConfig) -> None:
        """Test that factory function creates a valid server."""
        server = create_did_server(did_config)

        assert isinstance(server, DIDServer)
        assert server.app is not None
        assert server.key_manager is not None
        assert server.key_manager.config == did_config

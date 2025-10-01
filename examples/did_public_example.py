#!/usr/bin/env python3
"""
ANP Agent Client Example using docs/did_public/ DID documents

This example demonstrates how to connect to the ANP agent using the real
DID documents and private keys from the docs/did_public/ directory.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict

import httpx
from agent_connect.authentication import DIDWbaAuthHeader


class ANPAgentClient:
    """ANP Agent Client with DID-WBA Authentication."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client.
        
        Args:
            base_url: Base URL of the ANP agent service
        """
        self.base_url = base_url.rstrip('/')
        self.authenticator = None

        # Clear proxy settings that might interfere
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
            if key in os.environ:
                del os.environ[key]

    def setup_did_authentication(self):
        """Setup DID-WBA authentication using docs/did_public/ documents."""
        project_root = Path(__file__).parent.parent
        did_doc_path = project_root / "docs" / "did_public" / "public-did-doc.json"
        private_key_path = project_root / "docs" / "did_public" / "public-private-key.pem"

        if not did_doc_path.exists():
            raise FileNotFoundError(f"DID document not found: {did_doc_path}")
        if not private_key_path.exists():
            raise FileNotFoundError(f"Private key not found: {private_key_path}")

        print(f"📄 Using DID document: {did_doc_path}")
        print(f"🔑 Using private key: {private_key_path}")

        # Load and display DID document info
        with open(did_doc_path) as f:
            did_doc = json.load(f)

        print(f"🆔 DID: {did_doc.get('id')}")
        print(f"🔐 Verification methods: {len(did_doc.get('verificationMethod', []))}")

        self.authenticator = DIDWbaAuthHeader(
            did_document_path=str(did_doc_path),
            private_key_path=str(private_key_path),
        )

        return did_doc

    async def get_service_info(self) -> Dict[str, Any]:
        """Get basic service information (no auth required)."""
        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()

    async def get_agent_description(self) -> Dict[str, Any]:
        """Get agent description with DID-WBA authentication."""
        if not self.authenticator:
            raise ValueError("Authentication not setup. Call setup_did_authentication() first.")

        url = f"{self.base_url}/agents/test/ad.json"

        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Get authentication headers
            auth_headers = self.authenticator.get_auth_header(url, force_new=True)

            print(f"🔐 Authentication headers prepared for: {url}")
            print(f"📤 Authorization header: {auth_headers.get('Authorization', 'N/A')[:50]}...")

            # Make authenticated request
            response = await client.get(url, headers=auth_headers)
            response.raise_for_status()
            return response.json()

    async def explore_agent_interfaces(self, agent_desc: Dict[str, Any]):
        """Explore the agent's available interfaces."""
        print("\n🔍 Exploring Agent Interfaces")
        print("=" * 40)

        interfaces = agent_desc.get('interfaces', [])
        print(f"Found {len(interfaces)} interfaces:")

        for i, interface in enumerate(interfaces, 1):
            print(f"\n{i}. {interface.get('type', 'Unknown Type')}")
            print(f"   Protocol: {interface.get('protocol', 'N/A')}")
            print(f"   Version: {interface.get('version', 'N/A')}")
            print(f"   Description: {interface.get('description', 'No description')}")

            if interface.get('url'):
                print(f"   URL: {interface.get('url')}")

            # If it's an inline interface, show some details
            if 'content' in interface:
                content = interface['content']
                if isinstance(content, dict):
                    if 'methods' in content:
                        methods = content['methods']
                        print(f"   Methods: {len(methods)} available")
                        for method in methods[:3]:  # Show first 3 methods
                            print(f"     - {method.get('name')}: {method.get('summary', 'No summary')}")
                        if len(methods) > 3:
                            print(f"     ... and {len(methods) - 3} more")

    async def test_api_endpoints(self):
        """Test various API endpoints."""
        print("\n🧪 Testing API Endpoints")
        print("=" * 30)

        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Test health endpoint
            try:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    health = response.json()
                    print(f"✅ Health: {health.get('status')}")
                else:
                    print(f"❌ Health check failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Health check error: {e}")

            # Test API documentation
            try:
                response = await client.get(f"{self.base_url}/docs")
                if response.status_code == 200:
                    print("✅ API documentation available at /docs")
                else:
                    print(f"❌ API docs failed: {response.status_code}")
            except Exception as e:
                print(f"❌ API docs error: {e}")


async def main():
    """Main demonstration function."""
    print("🤖 ANP Agent Client - DID Public Example")
    print("=" * 50)

    client = ANPAgentClient()

    try:
        # 1. Get basic service info
        print("\n📋 Step 1: Getting service information...")
        service_info = await client.get_service_info()
        print(f"✅ Service: {service_info.get('service')}")
        print(f"✅ Version: {service_info.get('version')}")
        print(f"✅ Protocol: {service_info.get('protocol')} v{service_info.get('protocol_version')}")
        print(f"✅ Status: {service_info.get('status')}")

        # 2. Setup DID authentication
        print("\n🔐 Step 2: Setting up DID-WBA authentication...")
        did_doc = client.setup_did_authentication()
        print("✅ Authentication setup complete!")

        # 3. Get agent description with authentication
        print("\n🤖 Step 3: Getting agent description with DID-WBA auth...")
        agent_desc = await client.get_agent_description()
        print("✅ Agent description retrieved successfully!")

        print("\n📊 Agent Information:")
        print(f"   Name: {agent_desc.get('name')}")
        print(f"   DID: {agent_desc.get('did')}")
        print(f"   Protocol: {agent_desc.get('protocolType')} v{agent_desc.get('protocolVersion')}")
        print(f"   Owner: {agent_desc.get('owner', {}).get('name', 'N/A')}")
        print(f"   Created: {agent_desc.get('created')}")

        # 4. Explore interfaces
        await client.explore_agent_interfaces(agent_desc)

        # 5. Test other endpoints
        await client.test_api_endpoints()

        print("\n🎉 All tests completed successfully!")
        print("\n💡 Next steps:")
        print("   - Explore the OpenRPC interfaces")
        print("   - Try calling specific agent methods")
        print("   - Test the natural language interface")
        print("   - Check out the API documentation at http://localhost:8000/docs")

    except FileNotFoundError as e:
        print(f"❌ DID documents not found: {e}")
        print("\n💡 Make sure the following files exist:")
        print("   - docs/did_public/public-did-doc.json")
        print("   - docs/did_public/public-private-key.pem")
        return 1

    except httpx.ConnectError:
        print("❌ Cannot connect to ANP agent service")
        print("💡 Make sure the service is running:")
        print("   cd /Users/cs/work/anp-agent-example")
        print("   PYTHONPATH=src uv run python src/main.py")
        return 1

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    print("Starting ANP Agent DID Public Example...")
    print("This example uses the DID documents from docs/did_public/")
    print()

    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Example interrupted by user")
        exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        exit(1)

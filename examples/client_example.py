#!/usr/bin/env python3
"""
ANP Agent Client Example

This example demonstrates how to connect to the ANP agent's description endpoint
and retrieve agent metadata using DID-WBA authentication.
"""

import asyncio
import sys
from typing import Any, Dict

import httpx
from agent_connect.authentication import DIDWbaAuthHeader


class ANPAgentClient:
    """Client for connecting to ANP-compliant agents."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the ANP agent client.
        
        Args:
            base_url: Base URL of the ANP agent service
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient()
        self.authenticator = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    def setup_authentication(self, did_document_path: str, private_key_path: str):
        """Setup DID-WBA authentication.
        
        Args:
            did_document_path: Path to DID document JSON file
            private_key_path: Path to private key PEM file
        """
        self.authenticator = DIDWbaAuthHeader(
            did_document_path=did_document_path,
            private_key_path=private_key_path,
        )

    async def get_agent_description(self, agent_path: str = "/agents/test/ad.json") -> Dict[str, Any]:
        """Get agent description from the ANP agent.
        
        Args:
            agent_path: Path to the agent description endpoint
            
        Returns:
            Agent description JSON data
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = f"{self.base_url}{agent_path}"

        # Prepare headers
        headers = {"Content-Type": "application/json"}

        # Add authentication if configured
        if self.authenticator:
            auth_headers = self.authenticator.get_auth_header(url, force_new=True)
            headers.update(auth_headers)

        # Make the request
        response = await self.client.get(url, headers=headers)

        # Handle authentication challenges
        if response.status_code == 401 and self.authenticator:
            print("Authentication required, retrying with DID-WBA...")
            auth_headers = self.authenticator.get_auth_header(url, force_new=True)
            headers.update(auth_headers)
            response = await self.client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    async def get_service_info(self) -> Dict[str, Any]:
        """Get basic service information (no auth required).
        
        Returns:
            Service information JSON data
        """
        url = f"{self.base_url}/"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status (no auth required).
        
        Returns:
            Health status JSON data
        """
        url = f"{self.base_url}/health"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()


async def main():
    """Main example function."""
    print("🤖 ANP Agent Client Example")
    print("=" * 50)

    # Initialize client
    async with ANPAgentClient() as client:
        try:
            # 1. Get basic service info (no auth required)
            print("\n📋 Getting service information...")
            service_info = await client.get_service_info()
            print(f"Service: {service_info.get('service')}")
            print(f"Version: {service_info.get('version')}")
            print(f"Protocol: {service_info.get('protocol')} v{service_info.get('protocol_version')}")
            print(f"Status: {service_info.get('status')}")

            # 2. Get health status (no auth required)
            print("\n🏥 Getting health status...")
            health = await client.get_health_status()
            print(f"Health: {health.get('status')}")

            # 3. Try to get agent description without authentication
            print("\n🔓 Trying to get agent description without authentication...")
            try:
                agent_desc = await client.get_agent_description()
                print("✅ Success! Agent description retrieved without authentication.")
                print(f"Agent Name: {agent_desc.get('name')}")
                print(f"Agent DID: {agent_desc.get('did')}")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    print("❌ Authentication required (as expected)")
                    print("💡 To test with authentication, you need:")
                    print("   - DID document JSON file")
                    print("   - Private key PEM file")
                    print("   - Call client.setup_authentication(did_doc_path, key_path)")
                else:
                    print(f"❌ Unexpected error: {e}")

            # 4. Example with mock authentication (for demonstration)
            print("\n🔐 Example with Bearer token (mock authentication)...")
            try:
                headers = {"Authorization": "Bearer mock-token-for-demo"}
                url = f"{client.base_url}/agents/test/ad.json"
                response = await client.client.get(url, headers=headers)

                if response.status_code == 200:
                    agent_desc = response.json()
                    print("✅ Success! Agent description retrieved with mock token.")
                    print(f"Agent Name: {agent_desc.get('name')}")
                    print(f"Agent DID: {agent_desc.get('did')}")
                    print(f"Interfaces: {len(agent_desc.get('interfaces', []))} available")

                    # Show interface types
                    for i, interface in enumerate(agent_desc.get('interfaces', []), 1):
                        print(f"  {i}. {interface.get('type')} - {interface.get('protocol')}")

                else:
                    print(f"❌ Failed with status: {response.status_code}")

            except Exception as e:
                print(f"❌ Error: {e}")

        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("💡 Make sure the ANP agent service is running on http://localhost:8000")
            return 1

    print("\n✨ Example completed!")
    return 0


def print_usage():
    """Print usage information."""
    print("""
Usage: python client_example.py [OPTIONS]

This example demonstrates connecting to an ANP agent service.

Prerequisites:
1. Start the ANP agent service:
   cd /path/to/anp-agent-example
   uv run python src/main.py

2. The service should be running on http://localhost:8000

Example with DID-WBA authentication:
```python
async with ANPAgentClient() as client:
    client.setup_authentication(
        did_document_path="path/to/did-document.json",
        private_key_path="path/to/private-key.pem"
    )
    agent_desc = await client.get_agent_description()
```

For more information, see the ANP protocol documentation.
""")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print_usage()
        sys.exit(0)

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Quick test script for ANP Agent with DID-WBA authentication.

Usage: python examples/quick_test.py
"""

import asyncio
import os
from pathlib import Path

import httpx
from agent_connect.authentication import DIDWbaAuthHeader


async def quick_test():
    """Quick test of ANP agent with real DID authentication."""
    # Clear proxy settings
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
        if key in os.environ:
            del os.environ[key]

    base_url = "http://localhost:8000"

    # Setup DID authentication
    project_root = Path(__file__).parent.parent
    did_doc_path = project_root / "docs" / "did_public" / "public-did-doc.json"
    private_key_path = project_root / "docs" / "did_public" / "public-private-key.pem"

    print("🚀 Quick ANP Agent Test")
    print("=" * 30)

    try:
        # Setup authenticator
        authenticator = DIDWbaAuthHeader(
            did_document_path=str(did_doc_path),
            private_key_path=str(private_key_path),
        )

        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Test 1: Service info
            print("1️⃣ Service info...", end=" ")
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data.get('service')} v{data.get('version')}")
            else:
                print(f"❌ {response.status_code}")
                return

            # Test 2: Agent description with DID auth
            print("2️⃣ Agent description...", end=" ")
            url = f"{base_url}/agents/test/ad.json"
            auth_headers = authenticator.get_auth_header(url, force_new=True)

            response = await client.get(url, headers=auth_headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data.get('name')} ({len(data.get('interfaces', []))} interfaces)")
            else:
                print(f"❌ {response.status_code}")
                return

            print("\n🎉 All tests passed!")
            print(f"🌐 API docs: {base_url}/docs")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(quick_test())

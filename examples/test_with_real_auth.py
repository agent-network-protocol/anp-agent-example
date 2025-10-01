#!/usr/bin/env python3
"""
Test ANP Agent with Real DID-WBA Authentication

This example demonstrates how to connect to the ANP agent using real
DID-WBA authentication with the agent-connect library.
"""

import asyncio
import json
import os
from pathlib import Path

import httpx
from agent_connect.authentication import DIDWbaAuthHeader


async def test_with_real_auth():
    """Test ANP agent with real DID-WBA authentication."""
    print("🔐 Testing ANP Agent with Real DID-WBA Authentication")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Clear proxy settings
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
        if key in os.environ:
            del os.environ[key]
    
    # Check if we have DID documents and keys
    project_root = Path(__file__).parent.parent
    did_doc_path = project_root / "docs" / "did_public" / "public-did-doc.json"
    private_key_path = project_root / "docs" / "did_public" / "public-private-key.pem"
    
    print(f"\n📁 Looking for DID documents...")
    print(f"DID Document: {did_doc_path}")
    print(f"Private Key: {private_key_path}")
    
    if not did_doc_path.exists() or not private_key_path.exists():
        print("❌ DID documents not found. Creating mock authentication test...")
        await test_mock_authentication(base_url)
        return
    
    print("✅ DID documents found. Testing real authentication...")
    
    try:
        # Setup authenticator
        authenticator = DIDWbaAuthHeader(
            did_document_path=str(did_doc_path),
            private_key_path=str(private_key_path),
        )
        
        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Test authenticated request
            url = f"{base_url}/agents/travel/test/ad.json"
            
            print(f"\n🔑 Getting authentication headers for: {url}")
            auth_headers = authenticator.get_auth_header(url, force_new=True)
            
            print(f"📤 Making authenticated request...")
            response = await client.get(url, headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Success! Agent description retrieved with real DID-WBA auth.")
                print(f"Agent Name: {data.get('name')}")
                print(f"Agent DID: {data.get('did')}")
                print(f"Protocol: {data.get('protocolType')} v{data.get('protocolVersion')}")
                print(f"Interfaces: {len(data.get('interfaces', []))}")
                
                # Show available interfaces
                for i, interface in enumerate(data.get('interfaces', []), 1):
                    print(f"  {i}. {interface.get('type')} ({interface.get('protocol')})")
                    
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error during real authentication: {e}")
        print("💡 Falling back to mock authentication test...")
        await test_mock_authentication(base_url)


async def test_mock_authentication(base_url: str):
    """Test with mock authentication for demonstration."""
    print("\n🎭 Testing Mock Authentication")
    print("-" * 40)
    
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Test 1: No authentication (should fail)
        print("\n1️⃣ Testing without authentication...")
        try:
            response = await client.get(f"{base_url}/agents/travel/test/ad.json")
            if response.status_code == 401:
                print("✅ Correctly requires authentication")
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Mock Bearer token
        print("\n2️⃣ Testing with mock Bearer token...")
        try:
            # Create a simple mock JWT-like token for testing
            mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJ0ZXN0IiwiYXVkIjoidGVzdCIsImV4cCI6OTk5OTk5OTk5OX0.test"
            headers = {"Authorization": f"Bearer {mock_token}"}
            
            response = await client.get(f"{base_url}/agents/travel/test/ad.json", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Success with mock token!")
                print(f"Agent Name: {data.get('name')}")
                print(f"Agent DID: {data.get('did')}")
                
                # Show some interface details
                interfaces = data.get('interfaces', [])
                print(f"Available Interfaces: {len(interfaces)}")
                for interface in interfaces:
                    print(f"  - {interface.get('type')}: {interface.get('description', 'No description')}")
                    
            elif response.status_code == 401:
                print("❌ Mock token rejected (this is expected with real DID-WBA verification)")
                print("💡 To test successfully, you need real DID documents and keys")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def create_sample_did_documents():
    """Create sample DID documents for testing (for reference only)."""
    print("\n📝 Sample DID Document Structure (for reference):")
    
    sample_did_doc = {
        "id": "did:wba:example.com:service:test-agent",
        "verificationMethod": [
            {
                "id": "did:wba:example.com:service:test-agent#key-1",
                "type": "RsaVerificationKey2018",
                "controller": "did:wba:example.com:service:test-agent",
                "publicKeyPem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
            }
        ],
        "authentication": ["#key-1"],
        "service": [
            {
                "id": "#agent-service",
                "type": "AgentService",
                "serviceEndpoint": "https://example.com/agents/test"
            }
        ]
    }
    
    print(json.dumps(sample_did_doc, indent=2))
    
    print("\n🔑 To create real DID documents and keys:")
    print("1. Generate RSA key pair:")
    print("   openssl genrsa -out private-key.pem 2048")
    print("   openssl rsa -in private-key.pem -pubout -out public-key.pem")
    print("2. Create DID document with the public key")
    print("3. Use DIDWbaAuthHeader with the documents")


if __name__ == "__main__":
    print("Starting ANP Agent DID-WBA Authentication Test...")
    print("Make sure the agent is running: uv run python src/main.py")
    print()
    
    try:
        asyncio.run(test_with_real_auth())
        print("\n📚 For more information:")
        create_sample_did_documents()
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

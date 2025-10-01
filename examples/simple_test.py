#!/usr/bin/env python3
"""
Simple test script to verify ANP agent connectivity.

This is a minimal example that tests basic connectivity to the ANP agent
without requiring DID-WBA authentication setup.
"""

import asyncio
import json
import os

import httpx

# Clear proxy environment variables for this test
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
    if key in os.environ:
        del os.environ[key]


async def test_anp_agent():
    """Test basic connectivity to the ANP agent."""
    base_url = "http://localhost:8000"
    
    # Create client with timeout settings
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        print("🧪 Testing ANP Agent Connectivity")
        print("=" * 40)
        
        # Test 1: Service info
        print("\n1️⃣ Testing service info endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service: {data.get('service')}")
                print(f"✅ Version: {data.get('version')}")
                print(f"✅ Status: {data.get('status')}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Health check
        print("\n2️⃣ Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health: {data.get('status')}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Agent description (should require auth)
        print("\n3️⃣ Testing agent description endpoint...")
        try:
            response = await client.get(f"{base_url}/agents/travel/test/ad.json")
            if response.status_code == 200:
                print("⚠️  Unexpected: Got response without authentication")
                data = response.json()
                print(f"Agent: {data.get('name')}")
            elif response.status_code == 401:
                print("✅ Correctly requires authentication")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Agent description with mock token
        print("\n4️⃣ Testing with mock Bearer token...")
        try:
            headers = {"Authorization": "Bearer test-mock-jwt-token"}
            response = await client.get(f"{base_url}/agents/travel/test/ad.json", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print("✅ Success with mock token!")
                print(f"Agent Name: {data.get('name')}")
                print(f"Agent DID: {data.get('did')}")
                print(f"Protocol: {data.get('protocolType')} v{data.get('protocolVersion')}")
                print(f"Interfaces: {len(data.get('interfaces', []))}")
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: API documentation
        print("\n5️⃣ Testing API documentation...")
        try:
            response = await client.get(f"{base_url}/docs")
            if response.status_code == 200:
                print("✅ API docs available at /docs")
            else:
                print(f"❌ Docs failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    print("Starting ANP Agent connectivity test...")
    print("Make sure the agent is running: uv run python src/main.py")
    print()
    
    try:
        asyncio.run(test_anp_agent())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

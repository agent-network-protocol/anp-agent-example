#!/usr/bin/env python3
"""
Simple example showing how to use ANPCrawler to test the Remote Agent.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from local_agent import RemoteAgentClient  # noqa: E402


async def main():
    """Run simple agent test."""
    print("\n🧪 Simple Agent-to-Agent Test using ANPCrawler\n")

    client = RemoteAgentClient("http://localhost:8000")

    try:
        # Fetch agent description first
        print("Discovering remote agent...")
        await client.fetch_agent_description()
        print()

        # Test echo
        print("Test 1: Remote Echo")
        print("-" * 40)
        result = await client.test_echo("Hello from test!")
        if result.get('success'):
            echo_result = result.get('result', {})
            print(f"✅ Response: {echo_result.get('response')}\n")
        else:
            print(f"❌ Error: {result.get('error')}\n")

        # Test greet (if available)
        tools = await client.list_available_tools()
        if "greet" in tools:
            print("Test 2: Remote Greet")
            print("-" * 40)
            result = await client.test_greet("Alice")
            if result.get('success'):
                greet_result = result.get('result', {})
                print(f"✅ Message: {greet_result.get('message')}")
                print(f"   Session ID: {greet_result.get('session_id')}")
                print(f"   Visit Count: {greet_result.get('visit_count')}\n")
            else:
                print(f"❌ Error: {result.get('error')}\n")
        else:
            print("Test 2: Greet interface not discovered (link reference needs additional fetch)\n")

        print("✨ Test completed!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the remote agent is running:")
        print("  PYTHONPATH=src uv run python src/remote_agent.py")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

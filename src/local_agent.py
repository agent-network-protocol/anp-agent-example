#!/usr/bin/env python3
"""
ANP Local Agent - Client using ANPCrawler

This client uses ANPCrawler to discover and interact with the remote ANP agent.
It demonstrates:
- Fetching agent description
- Discovering available tools/interfaces
- Calling remote methods via ANPCrawler
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path for anp imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from anp.anp_crawler.anp_crawler import ANPCrawler  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RemoteAgentClient:
    """Client for crawling and interacting with remote ANP agent using ANPCrawler."""

    def __init__(self, agent_url: str = "http://localhost:8000"):
        """
        Initialize the client.

        Args:
            agent_url: Base URL of the remote agent
        """
        self.agent_url = agent_url.rstrip('/')
        self.agent_description_url = f"{self.agent_url}/agents/remote/ad.json"

        # Paths to DID document and private key
        self.did_document_path = str(project_root / "docs" / "did_public" / "public-did-doc.json")
        self.private_key_path = str(project_root / "docs" / "jwt_key" / "RS256-private.pem")

        # Initialize ANPCrawler
        self.crawler = ANPCrawler(
            did_document_path=self.did_document_path,
            private_key_path=self.private_key_path,
            cache_enabled=True
        )

        logger.info(f"Initialized RemoteAgentClient for {self.agent_url}")

    async def fetch_agent_description(self):
        """
        Fetch and display the remote agent description.

        Returns:
            Tuple of (content_json, interfaces_list)
        """
        logger.info("Fetching remote agent description...")

        try:
            # Use fetch_text method to get agent description
            content_json, interfaces_list = await self.crawler.fetch_text(self.agent_description_url)

            # Parse and display JSON content
            try:
                parsed_content = json.loads(content_json["content"])
                logger.info("="*60)
                logger.info("Remote Agent Description:")
                logger.info("="*60)
                logger.info(f"Name: {parsed_content.get('name')}")
                logger.info(f"DID: {parsed_content.get('did')}")
                logger.info(f"Description: {parsed_content.get('description')}")
                logger.info(f"Interfaces found: {len(interfaces_list)}")

                # Display discovered interfaces
                for i, interface in enumerate(interfaces_list, 1):
                    func_info = interface.get('function', {})
                    logger.info(f"\nInterface {i}:")
                    logger.info(f"  Name: {func_info.get('name', 'N/A')}")
                    logger.info(f"  Description: {func_info.get('description', 'N/A')}")

                    # Display parameters
                    parameters = func_info.get('parameters', {})
                    if parameters.get('properties'):
                        logger.info("  Parameters:")
                        for param_name, param_info in parameters['properties'].items():
                            param_type = param_info.get('type', 'unknown')
                            param_desc = param_info.get('description', 'No description')
                            logger.info(f"    - {param_name} ({param_type}): {param_desc}")

            except json.JSONDecodeError:
                logger.error("Failed to parse agent description as JSON")
                logger.info(content_json["content"])

            return content_json, interfaces_list

        except Exception as e:
            logger.error(f"Failed to fetch agent description: {str(e)}")
            raise

    async def list_available_tools(self):
        """
        List all available tools discovered by the crawler.

        Returns:
            List of tool names
        """
        tools = self.crawler.list_available_tools()

        logger.info("="*60)
        logger.info("Available Tools:")
        logger.info("="*60)

        if not tools:
            logger.info("No tools discovered")
            return []

        for i, tool_name in enumerate(tools, 1):
            logger.info(f"{i}. {tool_name}")

            # Get detailed tool information
            tool_info = self.crawler.get_tool_interface_info(tool_name)
            if tool_info:
                logger.info(f"   Method: {tool_info.get('method_name', 'N/A')}")
                logger.info(f"   Server: {tool_info.get('servers', 'N/A')}")

        return tools

    async def call_tool(self, tool_name: str, arguments: dict):
        """
        Call a remote tool using ANPCrawler.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        logger.info("="*60)
        logger.info(f"Calling tool: {tool_name}")
        logger.info(f"Arguments: {json.dumps(arguments, indent=2, ensure_ascii=False)}")
        logger.info("="*60)

        try:
            result = await self.crawler.execute_tool_call(tool_name, arguments)

            logger.info("Result:")
            logger.info(json.dumps(result, indent=2, ensure_ascii=False))

            return result

        except Exception as e:
            logger.error(f"Tool call failed: {str(e)}")
            raise

    async def test_echo(self, message: str):
        """
        Test the remote agent's echo method.

        Args:
            message: Message to echo

        Returns:
            Echo response
        """
        logger.info(f"Testing echo with message: {message}")

        # First ensure we have fetched the agent description
        if not self.crawler.list_available_tools():
            await self.fetch_agent_description()

        # Call the echo tool - wrap parameters in 'params' as expected by FastANP
        result = await self.call_tool("echo", {"params": {"message": message}})
        return result

    async def test_greet(self, name: str):
        """
        Test the remote agent's greet method.

        Args:
            name: Name for greeting

        Returns:
            Greeting response
        """
        logger.info(f"Testing greet with name: {name}")

        # First ensure we have fetched the agent description
        if not self.crawler.list_available_tools():
            await self.fetch_agent_description()

        # Call the greet tool - wrap parameters in 'params' as expected by FastANP
        result = await self.call_tool("greet", {"params": {"name": name}})
        return result

    def get_statistics(self):
        """
        Get crawler statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "visited_urls": list(self.crawler.get_visited_urls()),
            "cache_size": self.crawler.get_cache_size(),
            "available_tools": self.crawler.list_available_tools()
        }


async def main():
    """Main function to demonstrate the client."""
    logger.info("="*60)
    logger.info("ANP Local Agent - Testing Remote Agent")
    logger.info("="*60)
    logger.info("")

    client = RemoteAgentClient("http://localhost:8000")

    try:
        # Step 1: Fetch and display agent description
        logger.info("1️⃣  Fetching Remote Agent Description...")
        await client.fetch_agent_description()
        logger.info("")

        # Step 2: List available tools
        logger.info("2️⃣  Listing Available Tools...")
        tools = await client.list_available_tools()
        logger.info("")

        # Step 3: Test echo method
        if "echo" in tools:
            logger.info("3️⃣  Testing Echo Method...")
            await client.test_echo("Hello from ANPCrawler!")
            logger.info("")

        # Step 4: Test greet method
        if "greet" in tools:
            logger.info("4️⃣  Testing Greet Method...")
            await client.test_greet("Alice")
            logger.info("")

            # Test again to see session increment
            logger.info("5️⃣  Testing Greet Again (Session Test)...")
            await client.test_greet("Alice")
            logger.info("")

        # Step 5: Display statistics
        logger.info("="*60)
        logger.info("Session Statistics:")
        logger.info("="*60)
        stats = client.get_statistics()
        logger.info(f"Visited URLs: {len(stats['visited_urls'])}")
        logger.info(f"Cache entries: {stats['cache_size']}")
        logger.info(f"Available tools: {len(stats['available_tools'])}")
        logger.info("\nVisited URLs:")
        for url in stats['visited_urls']:
            logger.info(f"  - {url}")

        logger.info("\n" + "="*60)
        logger.info("✅ All tests completed successfully!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

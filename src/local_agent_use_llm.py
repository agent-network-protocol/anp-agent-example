#!/usr/bin/env python3
"""
LLM-driven Local Agent using ANPCrawler tools.

This module exposes a command-line workflow that sends high-level goals to an
OpenAI model, exposes ANPCrawler's fetch_text and execute_tool_call as tools,
and streams model-driven tool invocations until a final answer is produced.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI

# Ensure project root is in sys.path for ANP imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import after adjusting sys.path
from anp.anp_crawler.anp_crawler import ANPCrawler  # noqa: E402

logger = logging.getLogger(__name__)


class LLMLocalAgent:
    """LLM-driven orchestrator that delegates actions to ANPCrawler tools."""

    def __init__(
        self,
        agent_url: str,
        model: str,
        temperature: float,
        did_document_path: Path | None = None,
        private_key_path: Path | None = None,
    ) -> None:
        self.agent_url = agent_url.rstrip("/")
        self.agent_description_url = f"{self.agent_url}/agents/remote/ad.json"
        self.model = model
        self.temperature = temperature

        did_path = (
            did_document_path
            if did_document_path
            else project_root / "docs" / "did_public" / "public-did-doc.json"
        )
        key_path = (
            private_key_path
            if private_key_path
            else project_root / "docs" / "jwt_key" / "RS256-private.pem"
        )

        self.crawler = ANPCrawler(
            did_document_path=str(did_path),
            private_key_path=str(key_path),
            cache_enabled=True,
        )
        self.client = OpenAI()
        self.tools = self._build_tool_definitions()
        self.system_prompt = self._build_system_prompt()

        logger.debug(
            "Initialized LLMLocalAgent with agent_url=%s, model=%s", self.agent_url, self.model
        )

    def _build_system_prompt(self) -> str:
        """Compose the system prompt guiding the LLM's strategy."""
        return (
            f"You are an orchestration agent controlling ANPCrawler to interact with a remote ANP "
            f"service located at {self.agent_url}. Always begin by calling the fetch_text tool on the "
            f"agent description URL {self.agent_description_url} to discover available interfaces. When invoking "
            f"execute_tool_call, wrap remote parameters inside the 'params' key if required by the "
            f"target interface. Respond with concise JSON-formattable conclusions once you have the "
            f"necessary information. Avoid guessing and rely on the provided tools."
        )

    def _build_tool_definitions(self) -> list[dict[str, Any]]:
        """Expose ANPCrawler capabilities to the model."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "fetch_text",
                    "description": (
                        "Fetch structured documents through ANPCrawler. Use this to retrieve the "
                        "agent description or other JSON artifacts. The response includes raw "
                        "content plus any interface definitions discovered."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": (
                                    "Absolute URL to fetch using ANPCrawler. Use "
                                    f"{self.agent_description_url} to inspect the remote agent."
                                ),
                            }
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_tool_call",
                    "description": (
                        "Execute a remote interface discovered via ANPCrawler. Ensure you pass "
                        "arguments that match the interface schema, typically nested under "
                        "'params'."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tool_name": {
                                "type": "string",
                                "description": "Name of the interface method to execute.",
                            },
                            "arguments": {
                                "type": "object",
                                "description": (
                                    "JSON payload to send to the remote method. Provide {} when "
                                    "no parameters are required."
                                ),
                                "default": {},
                            },
                        },
                        "required": ["tool_name", "arguments"],
                    },
                },
            },
        ]

    async def run(self, prompt: str) -> str:
        """
        Drive a tool-augmented conversation with the LLM until it delivers a final response.

        Args:
            prompt: High-level instruction provided by the user.

        Returns:
            Final assistant message content.
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        while True:
            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                tools=self.tools,
                tool_choice="auto",
            )
            choice = completion.choices[0]
            message = choice.message

            assistant_payload: dict[str, Any] = {"role": "assistant"}
            if message.content:
                assistant_payload["content"] = message.content
            if message.tool_calls:
                assistant_payload["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ]

            messages.append(assistant_payload)

            if not message.tool_calls:
                final_content = message.content or ""
                logger.info("LLM response: %s", final_content)
                return final_content

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError as exc:
                    tool_result = {"error": f"Invalid JSON arguments: {exc}"}
                else:
                    tool_result = await self._invoke_tool(tool_name, args)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

    async def _invoke_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatch tool invocations to the appropriate ANPCrawler method."""
        if tool_name == "fetch_text":
            return await self._handle_fetch_text(args)
        if tool_name == "execute_tool_call":
            return await self._handle_execute_tool_call(args)
        return {"error": f"Unknown tool: {tool_name}"}

    async def _handle_fetch_text(self, args: dict[str, Any]) -> dict[str, Any]:
        """Wrap ANPCrawler.fetch_text for LLM consumption."""
        url = args.get("url")
        if not isinstance(url, str):
            return {"error": "fetch_text requires a string 'url' field."}

        try:
            content_json, interfaces = await self.crawler.fetch_text(url)
        except Exception as exc:  # noqa: BLE001
            logger.exception("fetch_text failed for %s", url)
            return {"error": f"fetch_text failed: {exc}"}

        return {
            "content": content_json,
            "interfaces": interfaces,
        }

    async def _handle_execute_tool_call(self, args: dict[str, Any]) -> dict[str, Any]:
        """Wrap ANPCrawler.execute_tool_call for LLM consumption."""
        tool = args.get("tool_name")
        payload = args.get("arguments", {})
        if not isinstance(tool, str):
            return {"error": "execute_tool_call requires 'tool_name' as string."}
        if not isinstance(payload, dict):
            return {"error": "execute_tool_call requires 'arguments' as object."}

        try:
            result = await self.crawler.execute_tool_call(tool, payload)
        except Exception as exc:  # noqa: BLE001
            logger.exception("execute_tool_call failed for %s", tool)
            return {"error": f"execute_tool_call failed: {exc}"}

        return {"result": result}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the local LLM agent."""
    parser = argparse.ArgumentParser(description="Run an LLM-driven local ANP agent.")
    parser.add_argument(
        "prompt",
        nargs="+",
        help="High-level instruction for the agent.",
    )
    parser.add_argument(
        "--agent-url",
        default="http://localhost:8000",
        help="Base URL of the remote ANP agent.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="OpenAI model identifier to use.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for the LLM.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> None:
    """Entry point for the asynchronous workflow."""
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    prompt = " ".join(args.prompt)
    agent = LLMLocalAgent(
        agent_url=args.agent_url,
        model=args.model,
        temperature=args.temperature,
    )

    final_response = await agent.run(prompt)
    print(final_response)


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")


if __name__ == "__main__":
    main()

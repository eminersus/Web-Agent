"""
Chat Service for handling chat completions with MCP tool integration

This service orchestrates:
1. Sending messages to OpenRouter LLM
2. Detecting when LLM wants to call tools
3. Executing tools via MCP server
4. Returning results back to LLM
5. Streaming everything to the client
"""

import logging
import json
import os
from typing import AsyncGenerator, Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Environment variable to control full tool response logging
LOG_FULL_TOOL_RESPONSES = (
    os.getenv("LOG_FULL_TOOL_RESPONSES", "false").lower() == "true"
)
TOOL_RESPONSE_LOG_LIMIT = int(os.getenv("TOOL_RESPONSE_LOG_LIMIT", "200"))


class ChatService:
    """Service for handling chat with tool execution"""

    def __init__(self, openrouter, mcp_client):
        self.openrouter = openrouter
        self.mcp_client = mcp_client

    async def stream_chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_iterations: int = 5,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion with automatic tool calling.

        This method:
        1. Sends messages to LLM with available tools
        2. If LLM wants to call a tool, executes it via MCP
        3. Sends tool results back to LLM
        4. Continues until LLM provides final response
        5. Streams all steps to client

        Args:
            messages: Conversation history
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            max_iterations: Max tool calling iterations to prevent infinite loops

        Yields:
            SSE formatted strings with chat data
        """
        # Get available tools from MCP server
        tools = await self._get_mcp_tools()
        logger.info(f"Retrieved {len(tools)} tools from MCP")

        # Convert to OpenAI tools format
        openai_tools = self._convert_tools_to_openai_format(tools)
        logger.info(f"Converted to {len(openai_tools)} OpenAI format tools")

        # Add system prompt if first message isn't already a system message
        current_messages = messages.copy()
        if not current_messages or current_messages[0].get("role") != "system":
            system_message = {"role": "system", "content": self._get_system_prompt()}
            current_messages.insert(0, system_message)
        else:
            # Enhance existing system message with product card instructions
            current_messages[0]["content"] = self._enhance_system_prompt(
                current_messages[0]["content"]
            )
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Chat iteration {iteration}/{max_iterations}")

            # Send to LLM
            full_response = ""
            tool_calls = []
            tool_call_accumulator = {}  # Accumulate streaming tool call chunks by index
            finish_reason = None

            async for chunk in self.openrouter.generate_chat_stream(
                messages=current_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=openai_tools if openai_tools else None,
            ):
                # Handle errors
                if chunk.get("error"):
                    yield self._format_sse("error", {"error": chunk["error"]})
                    return

                # Handle text tokens
                if chunk.get("token"):
                    token = chunk["token"]
                    full_response += token
                    yield self._format_sse("token", {"token": token})

                # Handle tool calls (streaming - need to accumulate chunks)
                if chunk.get("tool_calls"):
                    for tool_call_chunk in chunk["tool_calls"]:
                        index = tool_call_chunk.get("index", 0)

                        # Initialize accumulator for this index if needed
                        if index not in tool_call_accumulator:
                            tool_call_accumulator[index] = {
                                "id": tool_call_chunk.get("id", f"call_{index}"),
                                "type": tool_call_chunk.get("type", "function"),
                                "function": {"name": "", "arguments": ""},
                            }

                        # Accumulate function data
                        if "function" in tool_call_chunk:
                            func_chunk = tool_call_chunk["function"]
                            if "name" in func_chunk:
                                tool_call_accumulator[index]["function"]["name"] = (
                                    func_chunk["name"]
                                )
                            if "arguments" in func_chunk:
                                tool_call_accumulator[index]["function"][
                                    "arguments"
                                ] += func_chunk["arguments"]

                        # Update ID if provided in this chunk
                        if "id" in tool_call_chunk:
                            tool_call_accumulator[index]["id"] = tool_call_chunk["id"]

                # Handle completion
                if chunk.get("finish_reason"):
                    finish_reason = chunk["finish_reason"]

            # Convert accumulated tool calls to list
            if tool_call_accumulator:
                tool_calls = [
                    tool_call_accumulator[i]
                    for i in sorted(tool_call_accumulator.keys())
                ]
                logger.info(f"Accumulated {len(tool_calls)} complete tool calls")

            # If we have a text response and no tool calls, we're done
            if full_response and not tool_calls and finish_reason != "tool_calls":
                logger.info("Chat completed with text response")
                yield self._format_sse("done", {})
                return

            # If finish reason is stop and we have a response, we're done
            if finish_reason == "stop" and full_response:
                logger.info("Chat completed with stop reason")
                yield self._format_sse("done", {})
                return

            # If LLM wants to call tools
            if tool_calls or finish_reason == "tool_calls":
                logger.info(f"Processing {len(tool_calls)} tool call(s)")

                # IMPORTANT: For Claude/Anthropic, we need to add the assistant message
                # with the tool calls BEFORE adding tool results
                # Build the assistant message with tool calls
                assistant_content = full_response if full_response else ""

                # For Claude/OpenAI format compatibility, add assistant message
                # This ensures tool_result has corresponding tool_use
                if tool_calls:
                    current_messages.append(
                        {
                            "role": "assistant",
                            "content": assistant_content,
                            "tool_calls": tool_calls,
                        }
                    )

                # Execute each tool call
                tool_results = []
                for tool_call in tool_calls:
                    # Log the raw tool call for debugging
                    logger.info(f"Raw tool_call: {json.dumps(tool_call)}")

                    # Extract tool name - handle different formats
                    tool_name = (
                        tool_call.get("function", {}).get("name")
                        or tool_call.get("name")
                        or None
                    )

                    # Extract arguments - handle different formats
                    tool_args_str = (
                        tool_call.get("function", {}).get("arguments")
                        or tool_call.get("arguments")
                        or tool_call.get("input")
                        or "{}"
                    )

                    # Extract tool call ID
                    tool_id = tool_call.get("id", f"call_{len(tool_results)}")

                    try:
                        # Parse arguments
                        if isinstance(tool_args_str, str):
                            tool_args = json.loads(tool_args_str)
                        else:
                            tool_args = tool_args_str

                        # Notify client of tool call
                        tool_call_event = self._format_sse(
                            "tool_call",
                            {"id": tool_id, "name": tool_name, "arguments": tool_args},
                        )
                        logger.info(f"Sending tool_call event: {tool_call_event[:100]}")
                        yield tool_call_event

                        # Special handling for display_product_cards tool
                        # This tool is intercepted and never sent to MCP
                        if tool_name == "display_product_cards":
                            logger.info(
                                "Intercepting display_product_cards tool call for UI rendering"
                            )

                            # Extract products from arguments
                            products = tool_args.get("products", [])

                            # Handle case where LLM sends products as JSON string instead of array
                            if isinstance(products, str):
                                try:
                                    products = json.loads(products)
                                    logger.info(f"Parsed products from JSON string")
                                except json.JSONDecodeError as e:
                                    logger.error(
                                        f"Failed to parse products JSON string: {e}"
                                    )
                                    products = []

                            # Send special SSE event for product cards
                            product_cards_event = self._format_sse(
                                "product_cards",
                                {"products": products, "count": len(products)},
                            )
                            logger.info(
                                f"Sending product_cards event with {len(products)} products"
                            )
                            yield product_cards_event

                            # Create a success result to send back to LLM
                            result = {
                                "success": True,
                                "message": f"Displayed {len(products)} product(s) as cards in the UI",
                                "count": len(products),
                            }

                            # Notify client of result
                            tool_result_event = self._format_sse(
                                "tool_result",
                                {"id": tool_id, "name": tool_name, "result": result},
                            )
                            logger.info(
                                f"Sending tool_result event for display_product_cards"
                            )
                            yield tool_result_event

                            # Format tool result for OpenRouter
                            result_content = json.dumps(result)
                            tool_results.append(
                                {
                                    "tool_call_id": tool_id,
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": result_content,
                                }
                            )
                            logger.info(
                                f"Product cards displayed: {len(products)} products"
                            )

                        else:
                            # Normal tool execution via MCP
                            logger.info(f"Executing tool: {tool_name}")
                            result = await self._execute_mcp_tool(tool_name, tool_args)

                            # Notify client of result
                            tool_result_event = self._format_sse(
                                "tool_result",
                                {"id": tool_id, "name": tool_name, "result": result},
                            )
                            logger.info(
                                f"Sending tool_result event: {tool_result_event[:100]}"
                            )
                            yield tool_result_event

                            # Format tool result for OpenRouter
                            result_content = (
                                json.dumps(result)
                                if not isinstance(result, str)
                                else result
                            )
                            tool_results.append(
                                {
                                    "tool_call_id": tool_id,
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": result_content,
                                }
                            )
                            logger.info(f"Tool result added: {result_content[:200]}")

                    except Exception as e:
                        logger.error(
                            f"Error executing tool {tool_name}: {e}", exc_info=True
                        )
                        error_result = {"error": str(e)}

                        yield self._format_sse(
                            "tool_result",
                            {"id": tool_id, "name": tool_name, "result": error_result},
                        )

                        error_content = json.dumps(error_result)
                        tool_results.append(
                            {
                                "tool_call_id": tool_id,
                                "role": "tool",
                                "name": tool_name,
                                "content": error_content,
                            }
                        )
                        logger.info(f"Tool error result: {error_content[:200]}")

                # Add tool results to conversation
                current_messages.extend(tool_results)

                # Continue to next iteration (LLM will process tool results)
                continue

            # If we get here without tool calls or response, check if we got ANYTHING
            if full_response:
                # We got some response, even if incomplete
                logger.info(f"Got partial response: {full_response[:100]}")
                yield self._format_sse("done", {})
                return
            elif finish_reason and finish_reason != "tool_calls":
                # Stream finished but no content - this is completion
                logger.info(f"Finished with reason: {finish_reason}")
                yield self._format_sse("done", {})
                return
            else:
                logger.warning("Unexpected state: no response or tool calls")
                yield self._format_sse("error", {"error": "No response from LLM"})
                return

        # Max iterations reached - extract the last tool result and present it
        logger.warning(f"Max iterations ({max_iterations}) reached")

        # Try to extract useful information from tool results
        if tool_results and len(tool_results) > 0:
            last_result = tool_results[-1]
            result_content = last_result.get("content", "")
            tool_name = last_result.get("name", "unknown")

            try:
                # Try to parse the result
                result_data = (
                    json.loads(result_content)
                    if isinstance(result_content, str)
                    else result_content
                )

                # Create a helpful response based on the tool result
                if isinstance(result_data, dict):
                    if "error" in result_data:
                        response_text = f"I tried to use the {tool_name} tool but got an error: {result_data['error']}"
                    elif "result" in result_data:
                        response_text = (
                            f"Based on the {tool_name} tool: {result_data['result']}"
                        )
                    else:
                        response_text = f"The {tool_name} tool returned: {result_data}"
                else:
                    response_text = f"The {tool_name} tool returned: {result_data}"

                yield self._format_sse("token", {"token": response_text})
            except:
                # Fallback if parsing fails
                yield self._format_sse(
                    "token", {"token": f"Tool result: {result_content}"}
                )
        else:
            fallback_message = "I attempted to process your request but encountered an issue completing the response."
            yield self._format_sse("token", {"token": fallback_message})

        yield self._format_sse("done", {})

    async def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP server"""
        try:
            tools = await self.mcp_client.list_tools()
            logger.info(f"Retrieved {len(tools)} tools from MCP server")
            return tools
        except Exception as e:
            logger.error(f"Error getting MCP tools: {e}", exc_info=True)
            return []

    async def _execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool via MCP server"""
        try:
            result = await self.mcp_client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}: {e}", exc_info=True)
            raise

    def _convert_tools_to_openai_format(
        self, mcp_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert MCP tool definitions to OpenAI function calling format.

        MCP tools have a 'inputSchema' which is JSON Schema.
        OpenAI expects 'function' with 'parameters' (also JSON Schema).
        """
        if not mcp_tools:
            return []

        openai_tools = []
        for tool in mcp_tools:
            try:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "parameters": tool.get(
                            "inputSchema",
                            {"type": "object", "properties": {}, "required": []},
                        ),
                    },
                }
                openai_tools.append(openai_tool)
                # Log each tool for debugging
                logger.debug(
                    f"Tool {tool.get('name')}: {json.dumps(openai_tool, indent=2)}"
                )
            except Exception as e:
                logger.warning(f"Error converting tool {tool.get('name')}: {e}")
                continue

        logger.info(f"Converted {len(openai_tools)} tools to OpenAI format")
        if openai_tools:
            logger.info(f"Sample tool: {openai_tools[0]['function']['name']}")
        return openai_tools

    def _format_sse(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event"""
        return f"data: {json.dumps({**data, 'type': event_type})}\n\n"

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt with instructions for using display tools.

        Returns:
            System prompt string
        """
        return """You are a helpful eBay shopping assistant. You help users find products on eBay.

When displaying product results to users:
1. After using search_items to get eBay results, select the most relevant products (typically 5-10)
2. Use the display_product_cards tool to show products as visual cards in the UI
3. For each product in the display_product_cards call, format the data as:
   - title: The product title (from itemSummaries[].title)
   - price: Format as "$X.XX" using price.value and price.currency
   - image: The image URL (from image.imageUrl)
   - url: The product URL (from itemWebUrl)
   - itemId: The eBay item ID (from itemId)
   - condition: Item condition if available (from condition)
   - seller: Seller username (from seller.username)
   - location: Format as "City, Country" if available (from itemLocation)
   - shipping: Shipping info, note if it's free shipping

Example workflow:
User: "I want to buy a black laptop under $1000"
1. Call search_items with appropriate filters (q="black laptop", filter="price:[..1000]", limit=20)
2. Review the results and select the top 5-10 most relevant products
3. Call display_product_cards with the formatted product data
4. Provide a brief text summary explaining what you found

Always use display_product_cards when showing products to provide the best user experience."""

    def _enhance_system_prompt(self, existing_prompt: str) -> str:
        """
        Enhance an existing system prompt with product card instructions.

        Args:
            existing_prompt: The existing system prompt

        Returns:
            Enhanced system prompt
        """
        product_card_instructions = """

IMPORTANT - Product Display Instructions:
When showing eBay products or any shopping results, use the display_product_cards tool to render visual cards.
After searching with search_items, extract the most relevant products and call display_product_cards with:
- title, price (formatted as "$X.XX"), image URL, product URL, itemId, condition, seller, location, shipping info.
This provides users with a much better visual experience than text listings."""

        return existing_prompt + product_card_instructions

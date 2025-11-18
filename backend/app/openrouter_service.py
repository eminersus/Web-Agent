"""
OpenRouter Service for LLM Integration

Handles communication with OpenRouter API for chat completions with streaming support.
"""

import os
import httpx
import json
from typing import AsyncGenerator, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Configuration from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_TIMEOUT = float(os.getenv("OPENROUTER_TIMEOUT", "120.0"))
APP_URL = os.getenv("APP_URL", "http://localhost:3080")


class OpenRouterService:
    """Service for interacting with OpenRouter API"""
    
    def __init__(
        self,
        api_key: str = OPENROUTER_API_KEY,
        base_url: str = OPENROUTER_BASE_URL,
        default_model: str = OPENROUTER_DEFAULT_MODEL
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.client = httpx.AsyncClient(timeout=OPENROUTER_TIMEOUT)
    
    async def health_check(self) -> bool:
        """Check if OpenRouter service is available"""
        try:
            response = await self.client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenRouter health check failed: {e}")
            return False
    
    async def list_models(self) -> list:
        """List available models"""
        try:
            response = await self.client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def generate_chat_stream(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming chat response using OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools/functions available to the model
        
        Yields:
            Dict containing token data, tool calls, and metadata
        """
        url = f"{self.base_url}/chat/completions"
        
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": APP_URL,
            "X-Title": "Web-Agent-Backend"
        }
        
        logger.info(f"Chat completion with model: {model}")
        
        try:
            async with self.client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                    yield {
                        "error": f"OpenRouter API returned status {response.status_code}",
                        "done": True
                    }
                    return
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # OpenRouter uses SSE format: "data: {...}"
                    if line.startswith("data: "):
                        line = line[6:]  # Remove "data: " prefix
                    
                    if line == "[DONE]":
                        yield {"done": True}
                        break
                    
                    # Skip OpenRouter processing messages
                    if "OPENROUTER PROCESSING" in line:
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        
                        # Extract the delta from the response
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            finish_reason = choices[0].get("finish_reason")
                            
                            # Handle content (text tokens)
                            content = delta.get("content")
                            if content:
                                yield {
                                    "token": content,
                                    "done": False
                                }
                            
                            # Handle tool calls (streaming format)
                            tool_calls = delta.get("tool_calls")
                            if tool_calls:
                                # Log what we're receiving
                                logger.debug(f"Received tool_calls delta: {tool_calls}")
                                yield {
                                    "tool_calls": tool_calls,
                                    "done": False
                                }
                            
                            # Also check for full message tool_calls (non-streaming)
                            if not tool_calls and choices:
                                message = choices[0].get("message", {})
                                message_tool_calls = message.get("tool_calls")
                                if message_tool_calls:
                                    logger.debug(f"Received message tool_calls: {message_tool_calls}")
                                    yield {
                                        "tool_calls": message_tool_calls,
                                        "done": False
                                    }
                            
                            # Handle completion
                            if finish_reason:
                                yield {
                                    "finish_reason": finish_reason,
                                    "done": True
                                }
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode JSON chunk: {line[:100]} - {e}")
                        continue
        
        except httpx.TimeoutException:
            logger.error(f"OpenRouter request timed out after {OPENROUTER_TIMEOUT}s")
            yield {
                "error": "Request timed out",
                "done": True
            }
        except Exception as e:
            logger.error(f"Error during generation: {e}", exc_info=True)
            yield {
                "error": str(e),
                "done": True
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance
_openrouter_service: Optional[OpenRouterService] = None


def get_openrouter_service() -> OpenRouterService:
    """Get or create the global OpenRouter service instance"""
    global _openrouter_service
    if _openrouter_service is None:
        _openrouter_service = OpenRouterService()
    return _openrouter_service


async def cleanup_openrouter_service():
    """Cleanup the global OpenRouter service instance"""
    global _openrouter_service
    if _openrouter_service is not None:
        await _openrouter_service.close()
        _openrouter_service = None


"""
LLM Service for Ollama Integration

Handles communication with Ollama API for chat completions with streaming support.
"""

import os
import httpx
import json
from typing import AsyncGenerator, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Configuration from environment
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://llm:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120.0"))

class OllamaService:
    """Service for interacting with Ollama LLM API"""
    
    def __init__(self, base_url: str = LLM_BASE_URL, model: str = LLM_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=LLM_TIMEOUT)
    
    async def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/version")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> list:
        """List available models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming response from Ollama
        
        Args:
            prompt: User message/prompt
            system_prompt: Optional system prompt to guide the model
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        
        Yields:
            Dict containing token data and metadata
        """
        url = f"{self.base_url}/api/generate"
        
        # Build the request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
        
        # Add max tokens if specified
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        logger.info(f"Generating with model: {self.model}")
        
        try:
            async with self.client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"Ollama API error: {response.status_code} - {error_text}")
                    yield {
                        "error": f"LLM API returned status {response.status_code}",
                        "done": True
                    }
                    return
                
                # Stream tokens as they arrive
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        
                        # Check if this is the final chunk
                        if chunk.get("done", False):
                            # Final chunk contains metadata
                            yield {
                                "done": True,
                                "total_duration": chunk.get("total_duration"),
                                "load_duration": chunk.get("load_duration"),
                                "prompt_eval_count": chunk.get("prompt_eval_count"),
                                "eval_count": chunk.get("eval_count"),
                            }
                        else:
                            # Regular token chunk
                            token = chunk.get("response", "")
                            if token:
                                yield {
                                    "token": token,
                                    "done": False
                                }
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode JSON chunk: {line[:100]} - {e}")
                        continue
        
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {LLM_TIMEOUT}s")
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
    
    async def generate_chat_stream(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming chat response using the chat API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{"role": "user", "content": "Hello"}]
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Yields:
            Dict containing token data and metadata
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        logger.info(f"Chat completion with model: {self.model}")
        
        try:
            async with self.client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"Ollama chat API error: {response.status_code} - {error_text}")
                    yield {
                        "error": f"LLM API returned status {response.status_code}",
                        "done": True
                    }
                    return
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        
                        if chunk.get("done", False):
                            yield {
                                "done": True,
                                "total_duration": chunk.get("total_duration"),
                                "prompt_eval_count": chunk.get("prompt_eval_count"),
                                "eval_count": chunk.get("eval_count"),
                            }
                        else:
                            # Extract the message content
                            message = chunk.get("message", {})
                            token = message.get("content", "")
                            if token:
                                yield {
                                    "token": token,
                                    "done": False
                                }
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode JSON chunk: {e}")
                        continue
        
        except httpx.TimeoutException:
            logger.error(f"Ollama chat request timed out after {LLM_TIMEOUT}s")
            yield {
                "error": "Request timed out",
                "done": True
            }
        except Exception as e:
            logger.error(f"Error during chat generation: {e}", exc_info=True)
            yield {
                "error": str(e),
                "done": True
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance
_ollama_service: Optional[OllamaService] = None

def get_ollama_service() -> OllamaService:
    """Get or create the global Ollama service instance"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service

async def cleanup_ollama_service():
    """Cleanup the global Ollama service instance"""
    global _ollama_service
    if _ollama_service is not None:
        await _ollama_service.close()
        _ollama_service = None


import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger("fintrack.ai")


class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM providers (Gemini, OpenAI, Claude, etc.)."""

    @abstractmethod
    async def generate_structured_json(
        self,
        system_instruction: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a structured JSON response from the LLM."""
        pass


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Provider using asynchronous REST endpoint.
    Supports gemini-1.5-flash and gemini-1.5-pro with native JSON response mode.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key.strip() if api_key else ""
        self.model_name = model_name.strip() if model_name else "gemini-1.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    async def generate_structured_json(
        self,
        system_instruction: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_instruction}
                ]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
                "topP": 0.8,
            }
        }

        url = f"{self.base_url}?key={self.api_key}"

        async with httpx.AsyncClient(timeout=35.0) as client:
            response = await client.post(url, json=payload)

            if response.status_code != 200:
                logger.error(f"Gemini API error (HTTP {response.status_code}): {response.text}")
                raise RuntimeError(f"Gemini API returned HTTP {response.status_code}: {response.text}")

            res_data = response.json()
            candidates = res_data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini API returned no candidates.")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts:
                raise RuntimeError("Gemini API returned empty content.")

            raw_text = content_parts[0].get("text", "{}")
            try:
                parsed_json = json.loads(raw_text)
                return parsed_json
            except json.JSONDecodeError as exc:
                logger.error(f"Failed to decode Gemini JSON: {raw_text}")
                raise ValueError(f"Invalid JSON returned by Gemini: {exc}")


def get_llm_provider() -> Optional[BaseLLMProvider]:
    """
    Factory function to instantiate the configured LLM provider.
    Future providers (e.g. OpenAI, Claude) can be cleanly plugged in here.
    """
    provider = settings.AI_PROVIDER.lower().strip()
    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return None
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.AI_MODEL_NAME,
        )
    # Placeholder for future expansion:
    # elif provider == "openai":
    #     return OpenAIProvider(...)
    # elif provider == "claude":
    #     return ClaudeProvider(...)
    return None

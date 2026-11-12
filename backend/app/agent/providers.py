"""
AI Provider abstraction layer.
All providers implement the same interface so the agent loop
never needs to know which model it's talking to.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

import structlog

from app.config import AIProvider, settings
from app.security.credential_store import get_api_key

log = structlog.get_logger(__name__)


# ── Base class ────────────────────────────────────────────────────────────────

class BaseAIProvider(ABC):
    """Abstract AI provider. Implement chat() for each backend."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Send a conversation and return the model's text response."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the provider is reachable and configured."""


# ── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAIProvider(BaseAIProvider):
    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.openai_model

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        api_key = get_api_key("openai")
        if not api_key:
            raise RuntimeError(
                "OpenAI API key not configured. "
                "Set it in Settings → AI Provider → API Key."
            )

        try:
            from openai import AsyncOpenAI  # type: ignore
        except ImportError:
            raise RuntimeError("openai package is not installed. Run: pip install openai")

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def is_available(self) -> bool:
        return get_api_key("openai") is not None


# ── Anthropic ─────────────────────────────────────────────────────────────────

class AnthropicProvider(BaseAIProvider):
    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.anthropic_model

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        api_key = get_api_key("anthropic")
        if not api_key:
            raise RuntimeError(
                "Anthropic API key not configured. "
                "Set it in Settings → AI Provider → API Key."
            )

        try:
            import anthropic  # type: ignore
        except ImportError:
            raise RuntimeError("anthropic package is not installed. Run: pip install anthropic")

        # Separate system message from conversation
        system_content = ""
        conversation: list[dict[str, str]] = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                conversation.append(msg)

        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system_content,
            messages=conversation,  # type: ignore
        )
        return response.content[0].text if response.content else ""

    async def is_available(self) -> bool:
        return get_api_key("anthropic") is not None


# ── Google Gemini ─────────────────────────────────────────────────────────────

class GeminiProvider(BaseAIProvider):
    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.gemini_model

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        api_key = get_api_key("gemini")
        if not api_key:
            raise RuntimeError(
                "Gemini API key not configured. "
                "Set it in Settings → AI Provider → API Key."
            )

        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise RuntimeError("google-generativeai package is not installed. Run: pip install google-generativeai")

        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(self._model)

        # Convert messages to Gemini format
        prompt_parts = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            if role == "system":
                prompt_parts.append(f"[System]: {msg['content']}")
            else:
                prompt_parts.append(msg["content"])

        response = model_obj.generate_content(
            "\n\n".join(prompt_parts),
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text or ""

    async def is_available(self) -> bool:
        return get_api_key("gemini") is not None


# ── Groq ──────────────────────────────────────────────────────────────────────

class GroqProvider(BaseAIProvider):
    """
    Groq uses the OpenAI-compatible API format, so we reuse the openai SDK
    with a custom base_url pointing to api.groq.com.
    Supports models like: qwen/qwen3-8b-27b, llama-3.3-70b-versatile, etc.
    """

    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.groq_model
        self._base_url = settings.groq_base_url

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        api_key = get_api_key("groq")
        if not api_key:
            raise RuntimeError(
                "Groq API key not configured. "
                "Set it in Settings → AI Provider → API Key."
            )

        try:
            from openai import AsyncOpenAI  # type: ignore
        except ImportError:
            raise RuntimeError("openai package is not installed. Run: pip install openai")

        # Groq's API is OpenAI-compatible — just point base_url at Groq
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=self._base_url,
        )

        response = await client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def is_available(self) -> bool:
        return get_api_key("groq") is not None


# ── Ollama (local) ────────────────────────────────────────────────────────────

class OllamaProvider(BaseAIProvider):
    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        self._model = model or settings.ollama_model
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        try:
            import httpx  # type: ignore
        except ImportError:
            raise RuntimeError("httpx package is not installed. Run: pip install httpx")

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")

    async def is_available(self) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False


# ── Factory ───────────────────────────────────────────────────────────────────

def create_provider() -> BaseAIProvider:
    """Create the AI provider configured in settings."""
    mapping: dict[AIProvider, type[BaseAIProvider]] = {
        AIProvider.OPENAI:    OpenAIProvider,
        AIProvider.ANTHROPIC: AnthropicProvider,
        AIProvider.GEMINI:    GeminiProvider,
        AIProvider.OLLAMA:    OllamaProvider,
        AIProvider.GROQ:      GroqProvider,
    }
    provider_class = mapping.get(settings.ai_provider)
    if not provider_class:
        raise RuntimeError(f"Unknown AI provider: {settings.ai_provider}")

    log.info("ai_provider_created", provider=settings.ai_provider.value, model=settings.active_model)
    return provider_class()

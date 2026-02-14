"""
Vendor-Agnostic LLM Provider Service.

Provides a unified interface for multiple LLM providers including:
- ZAI (GLM-4, GLM-5) - DEFAULT
- OpenAI (GPT-4, GPT-4o, etc.)
- Anthropic (Claude models)
- OpenRouter (access to many models)
- Google (Gemini)
- Mistral

Default provider: ZAI GLM-5
"""

import json
import os
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field

from app.utils.exceptions import LLMServiceException
import structlog

logger = structlog.get_logger()


class ProviderType(str, Enum):
    """Supported LLM provider types."""
    ZAI = "zai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GOOGLE = "google"
    MISTRAL = "mistral"
    CUSTOM = "custom"


class MessageRole(str, Enum):
    """Message roles for LLM conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMConfig(BaseModel):
    """
    Configuration for LLM provider.

    Defaults to ZAI GLM-5 for cost-effective daily use.
    """
    provider: ProviderType = Field(
        default=ProviderType.ZAI,
        description="LLM provider type"
    )
    model: str = Field(
        default="glm-5",
        description="Model name"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key (overrides env var)"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL (overrides default)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Maximum tokens to generate"
    )
    timeout: int = Field(
        default=120,
        ge=1,
        description="Request timeout in seconds"
    )
    # Provider-specific options
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific options"
    )


class CompletionResponse(BaseModel):
    """Standard response from LLM completion."""
    content: str
    model: str
    provider: ProviderType
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class StreamChunk(BaseModel):
    """Single chunk from streaming response."""
    content: str
    delta: str
    finish_reason: Optional[str] = None


class LLMProvider:
    """
    Unified LLM provider supporting multiple vendors.

    Default: ZAI GLM-5 for cost-effective operation.

    Example:
        provider = LLMProvider()  # Uses ZAI GLM-5 by default
        response = await provider.complete([
            {"role": "user", "content": "Hello!"}
        ])

        # Use OpenAI
        config = LLMConfig(provider=ProviderType.OPENAI, model="gpt-4o")
        provider = LLMProvider(config)
    """

    # Provider-specific configurations
    PROVIDER_CONFIGS: Dict[ProviderType, Dict[str, Any]] = {
        ProviderType.ZAI: {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "default_model": "glm-5",
            "api_key_env": "ZAI_API_KEY",
            "header_prefix": "Bearer",
            "supports_streaming": True,
            "format": "openai",
        },
        ProviderType.OPENAI: {
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
            "header_prefix": "Bearer",
            "supports_streaming": True,
            "format": "openai",
        },
        ProviderType.ANTHROPIC: {
            "base_url": "https://api.anthropic.com/v1",
            "default_model": "claude-sonnet-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY",
            "header_prefix": "",  # Uses x-api-key
            "supports_streaming": True,
            "format": "anthropic",
        },
        ProviderType.OPENROUTER: {
            "base_url": "https://openrouter.ai/api/v1",
            "default_model": "anthropic/claude-sonnet-4",
            "api_key_env": "OPENROUTER_API_KEY",
            "header_prefix": "Bearer",
            "supports_streaming": True,
            "format": "openai",
            "extra_headers": {
                "HTTP-Referer": "https://laias.ai",
                "X-Title": "LAIAS Agent Generator"
            }
        },
        ProviderType.GOOGLE: {
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "default_model": "gemini-2.0-flash-exp",
            "api_key_env": "GOOGLE_API_KEY",
            "header_prefix": "",
            "supports_streaming": True,
            "format": "google",
        },
        ProviderType.MISTRAL: {
            "base_url": "https://api.mistral.ai/v1",
            "default_model": "mistral-large-latest",
            "api_key_env": "MISTRAL_API_KEY",
            "header_prefix": "Bearer",
            "supports_streaming": True,
            "format": "openai",
        },
    }

    # Runtime registry for custom providers
    _custom_providers: Dict[str, Dict[str, Any]] = {}

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM provider.

        Args:
            config: LLM configuration. Defaults to ZAI GLM-5.
        """
        self.config = config or self._default_config()
        self._client: Optional[httpx.AsyncClient] = None
        self._validate_config()

    @classmethod
    def _default_config(cls) -> LLMConfig:
        """Create default config from environment variables."""
        # Check for provider override
        provider_env = os.getenv("LLM_PROVIDER", "zai").lower()
        provider_map = {
            "zai": ProviderType.ZAI,
            "openai": ProviderType.OPENAI,
            "anthropic": ProviderType.ANTHROPIC,
            "openrouter": ProviderType.OPENROUTER,
            "google": ProviderType.GOOGLE,
            "mistral": ProviderType.MISTRAL,
        }
        provider = provider_map.get(provider_env, ProviderType.ZAI)

        # Check for model override
        model = os.getenv("LLM_MODEL")
        if not model:
            model = cls.PROVIDER_CONFIGS[provider]["default_model"]

        return LLMConfig(provider=provider, model=model)

    def _validate_config(self) -> None:
        """Validate configuration and get API key."""
        provider_type = self.config.provider

        # Handle custom providers
        if provider_type == ProviderType.CUSTOM:
            if self.config.base_url is None:
                raise ValueError("base_url required for custom provider")
            if self.config.api_key is None:
                raise ValueError("api_key required for custom provider")
            return

        # Built-in providers
        if provider_type not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider: {provider_type}")

        provider_config = self.PROVIDER_CONFIGS[provider_type]

        # Get API key from config or environment
        api_key = self.config.api_key
        if not api_key:
            env_var = provider_config["api_key_env"]
            api_key = os.getenv(env_var)

        if not api_key:
            raise LLMServiceException(
                f"API key not found for {provider_type.value}. "
                f"Set {provider_config['api_key_env']} environment variable "
                f"or pass api_key to config.",
                provider=provider_type.value
            )

        self._api_key = api_key
        self._base_url = self.config.base_url or provider_config["base_url"]

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            timeout = httpx.Timeout(self.config.timeout, connect=30)
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            self._client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        await self.close()

    async def complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> CompletionResponse:
        """
        Generate a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Override config values (temperature, max_tokens, etc.)

        Returns:
            CompletionResponse with generated content

        Raises:
            LLMServiceException: If request fails
        """
        # Merge kwargs with config
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        model = kwargs.get("model", self.config.model)

        provider_config = self.PROVIDER_CONFIGS.get(
            self.config.provider,
            self._custom_providers.get(self.config.provider.value, {})
        )
        format_type = provider_config.get("format", "openai")

        try:
            if format_type == "openai":
                return await self._complete_openai(
                    messages, model, temperature, max_tokens
                )
            elif format_type == "anthropic":
                return await self._complete_anthropic(
                    messages, model, temperature, max_tokens
                )
            elif format_type == "google":
                return await self._complete_google(
                    messages, model, temperature, max_tokens
                )
            else:
                raise ValueError(f"Unsupported format: {format_type}")

        except httpx.HTTPStatusError as e:
            logger.error(
                "LLM HTTP error",
                provider=self.config.provider.value,
                status=e.response.status_code,
                response=e.response.text[:500]
            )
            raise LLMServiceException(
                f"HTTP error from {self.config.provider.value}: {e.response.status_code}",
                provider=self.config.provider.value,
                original_error=e
            )
        except Exception as e:
            logger.error(
                "LLM request failed",
                provider=self.config.provider.value,
                error=str(e)
            )
            raise LLMServiceException(
                f"Request to {self.config.provider.value} failed: {str(e)}",
                provider=self.config.provider.value,
                original_error=e
            )

    async def _complete_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> CompletionResponse:
        """Complete using OpenAI-compatible API (ZAI, OpenAI, OpenRouter, Mistral)."""
        provider_config = self.PROVIDER_CONFIGS.get(
            self.config.provider,
            self._custom_providers.get(self.config.provider.value, {})
        )

        headers = {
            "Content-Type": "application/json",
        }

        # Add auth header
        header_prefix = provider_config.get("header_prefix", "Bearer")
        if header_prefix:
            headers["Authorization"] = f"{header_prefix} {self._api_key}"
        else:
            headers["Authorization"] = self._api_key

        # Add extra headers (e.g., OpenRouter)
        for key, value in provider_config.get("extra_headers", {}).items():
            headers[key] = value

        # Build request payload
        payload = {
            "model": model,
            "messages": self._format_messages_openai(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add any extra options
        payload.update(self.config.extra)

        url = f"{self._base_url}/chat/completions"

        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens")
        finish_reason = data["choices"][0].get("finish_reason")

        return CompletionResponse(
            content=content,
            model=model,
            provider=self.config.provider,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            raw_response=data
        )

    async def _complete_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> CompletionResponse:
        """Complete using Anthropic API."""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01"
        }

        # Separate system message
        system_message = ""
        api_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                api_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_message,
            "messages": api_messages,
        }

        if temperature != 1.0:  # Anthropic default
            payload["temperature"] = temperature

        url = f"{self._base_url}/messages"

        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        content = data["content"][0]["text"]
        tokens_used = data.get("usage", {}).get("input_tokens") + data.get("usage", {}).get("output_tokens", 0)
        finish_reason = data.get("stop_reason")

        return CompletionResponse(
            content=content,
            model=model,
            provider=self.config.provider,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            raw_response=data
        )

    async def _complete_google(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> CompletionResponse:
        """Complete using Google Gemini API."""
        # Google API uses API key as query parameter
        headers = {"Content-Type": "application/json"}

        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role_map = {"user": "user", "assistant": "model"}
                contents.append({
                    "role": role_map.get(msg["role"], "user"),
                    "parts": [{"text": msg["content"]}]
                })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        url = f"{self._base_url}/models/{model}:generateContent?key={self._api_key}"

        response = await self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens_used = data.get("usageMetadata", {}).get("totalTokenCount")

        return CompletionResponse(
            content=content,
            model=model,
            provider=self.config.provider,
            tokens_used=tokens_used,
            finish_reason=data["candidates"][0].get("finishReason"),
            raw_response=data
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Override config values

        Yields:
            StreamChunk with incremental content

        Raises:
            LLMServiceException: If request fails
        """
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        model = kwargs.get("model", self.config.model)

        provider_config = self.PROVIDER_CONFIGS.get(
            self.config.provider,
            self._custom_providers.get(self.config.provider.value, {})
        )

        if not provider_config.get("supports_streaming", False):
            # Fall back to non-streaming
            response = await self.complete(messages, temperature=temperature, max_tokens=max_tokens, model=model)
            yield StreamChunk(content=response.content, delta=response.content, finish_reason="stop")
            return

        format_type = provider_config.get("format", "openai")

        try:
            if format_type == "openai":
                async for chunk in self._stream_openai(messages, model, temperature, max_tokens):
                    yield chunk
            elif format_type == "anthropic":
                async for chunk in self._stream_anthropic(messages, model, temperature, max_tokens):
                    yield chunk
            else:
                # Fall back for unsupported streaming formats
                response = await self.complete(messages, temperature=temperature, max_tokens=max_tokens, model=model)
                yield StreamChunk(content=response.content, delta=response.content, finish_reason="stop")

        except Exception as e:
            logger.error("LLM stream failed", provider=self.config.provider.value, error=str(e))
            raise LLMServiceException(
                f"Stream from {self.config.provider.value} failed: {str(e)}",
                provider=self.config.provider.value,
                original_error=e
            )

    async def _stream_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> AsyncIterator[StreamChunk]:
        """Stream using OpenAI-compatible API."""
        provider_config = self.PROVIDER_CONFIGS.get(
            self.config.provider,
            self._custom_providers.get(self.config.provider.value, {})
        )

        headers = {
            "Content-Type": "application/json",
        }

        header_prefix = provider_config.get("header_prefix", "Bearer")
        if header_prefix:
            headers["Authorization"] = f"{header_prefix} {self._api_key}"
        else:
            headers["Authorization"] = self._api_key

        for key, value in provider_config.get("extra_headers", {}).items():
            headers[key] = value

        payload = {
            "model": model,
            "messages": self._format_messages_openai(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        payload.update(self.config.extra)

        url = f"{self._base_url}/chat/completions"

        async with self.client.stream("POST", url, json=payload, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        yield StreamChunk(content="", delta="", finish_reason="stop")
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        finish_reason = data["choices"][0].get("finish_reason")
                        if content or finish_reason:
                            yield StreamChunk(
                                content=content,
                                delta=content,
                                finish_reason=finish_reason
                            )
                    except json.JSONDecodeError:
                        continue

    async def _stream_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> AsyncIterator[StreamChunk]:
        """Stream using Anthropic API."""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01"
        }

        system_message = ""
        api_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                api_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_message,
            "messages": api_messages,
            "stream": True,
        }

        if temperature != 1.0:
            payload["temperature"] = temperature

        url = f"{self._base_url}/messages"

        async with self.client.stream("POST", url, json=payload, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        if data["type"] == "content_block_delta":
                            delta = data.get("delta", {})
                            content = delta.get("text", "")
                            if content:
                                yield StreamChunk(
                                    content=content,
                                    delta=content
                                )
                        elif data["type"] == "message_stop":
                            yield StreamChunk(content="", delta="", finish_reason="stop")
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue

    def _format_messages_openai(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for OpenAI-compatible APIs."""
        formatted = []
        for msg in messages:
            role = msg["role"]
            if role not in ("system", "user", "assistant"):
                role = "user"
            formatted.append({"role": role, "content": msg["content"]})
        return formatted

    @classmethod
    def register_provider(
        cls,
        provider_type: str,
        config: Dict[str, Any]
    ) -> None:
        """
        Register a custom provider.

        Args:
            provider_type: Unique identifier for the provider
            config: Provider configuration dict with:
                - base_url: API base URL
                - default_model: Default model name
                - header_prefix: Auth header prefix (e.g., "Bearer")
                - format: "openai", "anthropic", or "google"
                - supports_streaming: Boolean
                - extra_headers: Optional dict of extra headers

        Example:
            LLMProvider.register_provider("myapi", {
                "base_url": "https://api.example.com/v1",
                "default_model": "my-model-1",
                "header_prefix": "Bearer",
                "format": "openai",
                "supports_streaming": True
            })

            provider = LLMProvider(LLMConfig(
                provider=ProviderType.CUSTOM,
                base_url="https://api.example.com/v1",
                model="my-model-1",
                api_key="sk-..."
            ))
        """
        required_keys = {"base_url", "default_model", "format"}
        missing = required_keys - config.keys()
        if missing:
            raise ValueError(f"Missing required config keys: {missing}")

        config.setdefault("header_prefix", "Bearer")
        config.setdefault("supports_streaming", False)
        config.setdefault("extra_headers", {})

        cls._custom_providers[provider_type] = config
        logger.info("Registered custom LLM provider", provider=provider_type)

    @classmethod
    def list_providers(cls) -> Dict[str, Dict[str, str]]:
        """
        List all available providers.

        Returns:
            Dict mapping provider names to their configs
        """
        result = {}
        for pt, config in cls.PROVIDER_CONFIGS.items():
            if pt != ProviderType.CUSTOM:
                result[pt.value] = {
                    "default_model": config["default_model"],
                    "api_key_env": config["api_key_env"],
                    "format": config["format"],
                }
        for name, config in cls._custom_providers.items():
            result[name] = {
                "default_model": config["default_model"],
                "format": config["format"],
                "custom": True,
            }
        return result


# Convenience functions for common use cases

async def complete(
    messages: List[Dict[str, str]],
    provider: Optional[ProviderType] = None,
    model: Optional[str] = None,
    **kwargs
) -> str:
    """
    Quick completion helper.

    Args:
        messages: Message list
        provider: Provider override
        model: Model override
        **kwargs: Additional config overrides

    Returns:
        Generated text content
    """
    config = LLMConfig()
    if provider:
        config.provider = provider
    if model:
        config.model = model

    async with LLMProvider(config) as llm:
        response = await llm.complete(messages, **kwargs)
        return response.content


def get_provider(
    provider: Optional[ProviderType] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Get a configured LLM provider instance.

    Args:
        provider: Provider type (defaults to ZAI)
        model: Model name
        **kwargs: Additional config options

    Returns:
        LLMProvider instance
    """
    config = LLMConfig()
    if provider:
        config.provider = provider
    if model:
        config.model = model
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return LLMProvider(config)

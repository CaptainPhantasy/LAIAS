"""
LLM Service for Agent Generator.

Handles communication with multiple LLM providers through the
vendor-agnostic LLMProvider for code generation with retry logic
and error handling.

Default provider: ZAI GLM-5
"""

import json
from typing import Optional, Dict, Any, List

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

from app.config import settings
from app.utils.exceptions import LLMServiceException
from app.services.llm_provider import (
    LLMProvider,
    LLMConfig,
    ProviderType,
    CompletionResponse,
)

logger = structlog.get_logger()


class LLMService:
    """
    Service for LLM-powered code generation.

    Supports multiple providers through the vendor-agnostic LLMProvider:
    - ZAI (GLM-4, GLM-5) - DEFAULT
    - OpenAI (GPT-4, GPT-4o, etc.)
    - Anthropic (Claude models)
    - OpenRouter (access to many models)
    - Google (Gemini)
    - Mistral

    Features:
    - Automatic retry on transient failures
    - Structured output parsing
    - Error handling and logging
    - Streaming support
    """

    def __init__(self):
        """Initialize LLM service."""
        # Determine default provider from settings or availability
        self._default_provider = self._determine_default_provider()
        self._default_model = self._determine_default_model()

        logger.info(
            "LLM Service initialized",
            default_provider=self._default_provider.value,
            default_model=self._default_model
        )

    def _determine_default_provider(self) -> ProviderType:
        """Determine default provider from settings."""
        provider_str = settings.LLM_PROVIDER.lower()
        provider_map = {
            "zai": ProviderType.ZAI,
            "portkey": ProviderType.PORTKEY,
            "openai": ProviderType.OPENAI,
            "anthropic": ProviderType.ANTHROPIC,
            "openrouter": ProviderType.OPENROUTER,
            "google": ProviderType.GOOGLE,
            "mistral": ProviderType.MISTRAL,
        }
        return provider_map.get(provider_str, ProviderType.ZAI)

    def _determine_default_model(self) -> str:
        """Determine default model from settings."""
        if settings.LLM_MODEL:
            return settings.LLM_MODEL
        return LLMProvider.PROVIDER_CONFIGS[self._default_provider]["default_model"]

    def _get_provider(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **config_kwargs
    ) -> LLMProvider:
        """
        Get a configured LLM provider instance.

        Args:
            provider: Provider name (defaults to configured default)
            model: Model name (defaults to provider's default)
            **config_kwargs: Additional config options

        Returns:
            Configured LLMProvider instance
        """
        provider_type = self._default_provider
        if provider:
            provider_map = {
                "zai": ProviderType.ZAI,
                "portkey": ProviderType.PORTKEY,
                "openai": ProviderType.OPENAI,
                "anthropic": ProviderType.ANTHROPIC,
                "openrouter": ProviderType.OPENROUTER,
                "google": ProviderType.GOOGLE,
                "mistral": ProviderType.MISTRAL,
            }
            provider_type = provider_map.get(provider.lower(), self._default_provider)

        config = LLMConfig(
            provider=provider_type,
            model=model or self._default_model,
            temperature=config_kwargs.get("temperature", settings.temperature),
            max_tokens=config_kwargs.get("max_tokens", settings.max_tokens),
            timeout=config_kwargs.get("timeout", settings.timeout_seconds),
        )

        return LLMProvider(config)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((LLMServiceException,))
    )
    async def generate_code(
        self,
        description: str,
        agent_name: str,
        complexity: str,
        task_type: str,
        tools_requested: Optional[List[str]] = None,
        provider: str = None,
        model: Optional[str] = None,
        include_memory: bool = True,
        include_analytics: bool = True,
        max_agents: int = 4,
        few_shot_examples: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate agent code using LLM.

        Args:
            description: Natural language description
            agent_name: Name for the flow class
            complexity: Complexity level
            task_type: Task category
            tools_requested: Specific tools to include
            provider: LLM provider (zai, openai, anthropic, etc.)
            model: Model override
            include_memory: Enable memory in agents
            include_analytics: Include analytics service
            max_agents: Maximum number of agents
            few_shot_examples: Example generations to include

        Returns:
            Dictionary with generated code and metadata

        Raises:
            LLMServiceException: If generation fails
        """
        # Build messages
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(
            description=description,
            agent_name=agent_name,
            complexity=complexity,
            task_type=task_type,
            tools_requested=tools_requested,
            include_memory=include_memory,
            include_analytics=include_analytics,
            max_agents=max_agents
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Add few-shot examples if provided
        if few_shot_examples:
            for example in few_shot_examples:
                messages.append({
                    "role": "user",
                    "content": example.get("description", "")
                })
                messages.append({
                    "role": "assistant",
                    "content": json.dumps(example.get("output", {}))
                })

        messages.append({"role": "user", "content": user_prompt})

        # Determine provider and model
        provider_name = provider or self._default_provider.value
        model_name = model or self._get_model_for_provider(provider_name)

        logger.info(
            "Generating agent code",
            provider=provider_name,
            model=model_name,
            complexity=complexity,
            task_type=task_type,
            max_agents=max_agents
        )

        try:
            llm = self._get_provider(provider=provider, model=model_name)
            response = await llm.complete(messages)

            logger.info(
                "LLM response received",
                provider=response.provider.value,
                model=response.model,
                tokens_used=response.tokens_used
            )

            return self._parse_response(response.content)

        except LLMServiceException:
            raise
        except Exception as e:
            logger.error("LLM generation failed", provider=provider_name, error=str(e))
            raise LLMServiceException(
                f"Failed to generate code: {str(e)}",
                provider=provider_name,
                original_error=e
            )

    def _get_model_for_provider(self, provider: str) -> str:
        """Get default model for a provider."""
        provider_map = {
            "zai": "glm-5",
            "portkey": "@zhipu/glm-4.7-flashx",
            "openai": "gpt-4o",
            "anthropic": "claude-sonnet-4-20250514",
            "openrouter": "anthropic/claude-sonnet-4",
            "google": "gemini-2.0-flash-exp",
            "mistral": "mistral-large-latest",
        }
        return provider_map.get(provider.lower(), "glm-5")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for code generation."""
        from app.prompts.system_prompts import CODE_GENERATION_SYSTEM_PROMPT
        return CODE_GENERATION_SYSTEM_PROMPT

    def _build_user_prompt(
        self,
        description: str,
        agent_name: str,
        complexity: str,
        task_type: str,
        tools_requested: Optional[List[str]],
        include_memory: bool,
        include_analytics: bool,
        max_agents: int
    ) -> str:
        """Build the user prompt for code generation."""
        tools_str = ", ".join(tools_requested) if tools_requested else "auto-select based on task"

        return f"""Generate a production-ready CrewAI agent flow based on this specification:

**Agent Name:** {agent_name}
**Description:** {description}
**Complexity Level:** {complexity}
**Task Type:** {task_type}
**Requested Tools:** {tools_str}
**Max Agents:** {max_agents}
**Include Memory:** {include_memory}
**Include Analytics:** {include_analytics}

Generate complete implementation following Godzilla architectural pattern EXACTLY.

Return a JSON object with these keys:
- flow_code: Complete, runnable Python code for the flow class
- state_class: The AgentState class definition (Pydantic BaseModel)
- agents_yaml: YAML configuration for all agents
- requirements: List of pip packages needed (crewai[tools], pydantic, structlog, etc.)
- flow_diagram: Mermaid diagram showing flow transitions
- agents_info: List of objects with role, goal, tools, llm_config for each agent

IMPORTANT: The flow_code must be complete, runnable Python code with NO placeholders or TODOs.
"""

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")

            # Try to extract JSON from markdown code blocks
            from app.utils.helpers import extract_code_from_markdown
            extracted = extract_code_from_markdown(content)
            try:
                return json.loads(extracted)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON response from LLM")

    async def check_health(self) -> Dict[str, str]:
        """
        Check health of configured LLM providers.

        Returns:
            Dict mapping provider names to status strings
        """
        status = {}
        providers_to_check = [
            ("portkey", ProviderType.PORTKEY, "@zhipu/glm-4.7-flashx"),
            ("zai", ProviderType.ZAI, "glm-5"),
            ("openai", ProviderType.OPENAI, "gpt-4o-mini"),
            ("anthropic", ProviderType.ANTHROPIC, "claude-3-haiku-20240307"),
        ]

        for name, provider_type, test_model in providers_to_check:
            try:
                config = LLMConfig(provider=provider_type, model=test_model, max_tokens=5)
                async with LLMProvider(config) as llm:
                    await llm.complete([{"role": "user", "content": "ping"}])
                status[name] = "ok"
            except LLMServiceException as e:
                status[name] = f"error: {str(e)[:50]}"
            except Exception as e:
                status[name] = f"error: {str(e)[:50]}"

        return status

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Stream a completion for the given messages.

        Args:
            messages: List of message dicts
            provider: Provider override
            model: Model override
            **kwargs: Additional config options

        Yields:
            StreamChunk objects with incremental content
        """
        llm = self._get_provider(provider=provider, model=model, **kwargs)
        async for chunk in llm.stream(messages, **kwargs):
            yield chunk

    async def complete(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: Optional[str] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Get a completion for the given messages.

        Args:
            messages: List of message dicts
            provider: Provider override
            model: Model override
            **kwargs: Additional config options

        Returns:
            CompletionResponse with generated content
        """
        llm = self._get_provider(provider=provider, model=model, **kwargs)
        return await llm.complete(messages, **kwargs)


# Global service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def reset_llm_service() -> None:
    """Reset the global LLM service instance (useful for testing)."""
    global _llm_service
    _llm_service = None

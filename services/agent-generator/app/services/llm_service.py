"""
LLM Service for Agent Generator.

Handles communication with multiple LLM providers through the
vendor-agnostic LLMProvider for code generation with retry logic
and error handling.

Default provider: Portkey -> GPT-4o
"""

import json
import os
from typing import Any

import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.services.llm_provider import (
    CompletionResponse,
    LLMConfig,
    LLMProvider,
    ProviderType,
)
from app.utils.exceptions import LLMServiceException

logger = structlog.get_logger()


class LLMService:
    """
    Service for LLM-powered code generation.

    Supports multiple providers through the vendor-agnostic LLMProvider:
    - ZAI (GLM-4, GLM-4.7-Flash) - DEFAULT
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
            default_model=self._default_model,
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
        self, provider: str | None = None, model: str | None = None, **config_kwargs
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

        # Use the selected provider's default model, not the global default
        provider_default = LLMProvider.PROVIDER_CONFIGS.get(provider_type, {}).get(
            "default_model", self._default_model
        )
        resolved_model = model if model and model.lower() != "default" else provider_default

        config = LLMConfig(
            provider=provider_type,
            model=resolved_model,
            temperature=config_kwargs.get("temperature", settings.temperature),
            max_tokens=config_kwargs.get("max_tokens", settings.max_tokens),
            timeout=config_kwargs.get("timeout", settings.timeout_seconds),
        )

        return LLMProvider(config)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((LLMServiceException,)),
    )
    async def generate_code(
        self,
        description: str,
        agent_name: str,
        complexity: str,
        task_type: str,
        tools_requested: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        include_memory: bool = True,
        include_analytics: bool = True,
        max_agents: int = 4,
        few_shot_examples: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
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
            max_agents=max_agents,
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Add few-shot examples if provided
        if few_shot_examples:
            for example in few_shot_examples:
                messages.append({"role": "user", "content": example.get("description", "")})
                messages.append(
                    {"role": "assistant", "content": json.dumps(example.get("output", {}))}
                )

        messages.append({"role": "user", "content": user_prompt})

        provider_name = provider or self._default_provider.value
        fallback_chain = self._build_fallback_chain(provider_name)

        last_error: Exception | None = None
        for attempt_provider in fallback_chain:
            attempt_model = (
                model
                if model and model.lower() != "default" and attempt_provider == provider_name
                else self._get_model_for_provider(attempt_provider)
            )

            logger.info(
                "Generating agent code",
                provider=attempt_provider,
                model=attempt_model,
                complexity=complexity,
                task_type=task_type,
                max_agents=max_agents,
            )

            try:
                llm = self._get_provider(provider=attempt_provider, model=attempt_model)
                response = await llm.complete(messages)

                logger.info(
                    "LLM response received",
                    provider=response.provider.value,
                    model=response.model,
                    tokens_used=response.tokens_used,
                )

                parsed = self._parse_response(response.content)
                # Post-process the generated flow_code: ensure every LLM()
                # constructor carries the Portkey virtual-key header and the
                # 'openai/' model prefix. The LLM template shows this, but
                # code-generation models sometimes omit fields during long
                # outputs. This deterministic fix prevents a downstream 401
                # inside the deployed container.
                if isinstance(parsed, dict) and "flow_code" in parsed:
                    parsed["flow_code"] = _postprocess_flow_code(parsed["flow_code"])
                return parsed

            except (LLMServiceException, Exception) as e:
                error_detail = str(e) or f"{type(e).__name__} (no message)"
                logger.warning(
                    "Provider failed, trying next",
                    failed_provider=attempt_provider,
                    error=error_detail,
                    remaining=len(fallback_chain) - fallback_chain.index(attempt_provider) - 1,
                )
                last_error = e

        raise LLMServiceException(
            f"All providers failed. Last error: {str(last_error)}",
            provider=provider_name,
            original_error=last_error,
        )

    def _build_fallback_chain(self, primary: str) -> list[str]:
        """Build ordered provider fallback chain, skipping unconfigured providers."""
        availability = {
            "portkey": settings.portkey_available,
            "zai": settings.zai_available,
            "openai": settings.openai_available,
            "anthropic": settings.anthropic_available,
            "openrouter": settings.openrouter_available,
            "google": settings.google_available,
            "mistral": settings.mistral_available,
        }
        preferred_order = ["portkey", "openai", "anthropic", "openrouter", "zai", "google", "mistral"]
        chain = [primary] if availability.get(primary, False) else []
        for p in preferred_order:
            if p != primary and availability.get(p, False):
                chain.append(p)
        if not chain:
            chain = [primary]
        return chain

    def _get_model_for_provider(self, provider: str) -> str:
        # LLM_MODEL env var overrides the per-provider default. This is
        # required when routing Portkey through a non-OpenAI virtual key
        # (e.g. portkeyclaude → Anthropic); the hardcoded 'gpt-4o' below
        # would 404 against an Anthropic-bound virtual key.
        env_override = os.getenv("LLM_MODEL", "").strip()
        if env_override:
            return env_override
        provider_map = {
            "portkey": os.getenv(
                "PORTKEY_HEALTH_MODEL", "claude-haiku-4-5-20251001"
            ),
            "zai": "glm-4.7-flash",
            "openai": "gpt-4o",
            "anthropic": "claude-sonnet-4-20250514",
            "openrouter": "anthropic/claude-sonnet-4",
            "google": "gemini-2.0-flash-exp",
            "mistral": "mistral-large-latest",
        }
        return provider_map.get(provider.lower(), "gpt-4o")

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
        tools_requested: list[str] | None,
        include_memory: bool,
        include_analytics: bool,
        max_agents: int,
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

OUTPUT INSTRUMENTATION REQUIREMENTS:
- Include an output router that reads LAIAS_OUTPUT_CONFIG and LAIAS_OUTPUT_ROOT.
- Register CrewAI event bus listeners when available and emit structured events.
- Provide task_callback and step_callback for Crew executions.
- Write per-run artifacts: summary.md, events.jsonl, metrics.json.
- Post structured events to LAIAS_OUTPUT_INGEST_URL when postgres output is enabled.
"""

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse LLM response into structured data.

        Handles multiple response formats:
        1. Direct JSON
        2. JSON wrapped in markdown code blocks (```json ... ```)
        3. JSON with broken escape sequences (common with some models)
        """
        # Attempt 1: Direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.debug("Direct JSON parse failed, trying markdown extraction", error=str(e))

        # Attempt 2: Extract from markdown code blocks
        from app.utils.helpers import extract_code_from_markdown

        extracted = extract_code_from_markdown(content)
        try:
            return json.loads(extracted)
        except json.JSONDecodeError as e:
            logger.debug("Markdown extraction JSON parse failed, trying escape fix", error=str(e))

        # Attempt 3: Fix common escape issues (models sometimes double-escape
        # or produce invalid escape sequences inside JSON string values)
        import re

        try:
            # Find the outermost JSON object
            match = re.search(r"\{.*\}", extracted, re.DOTALL)
            if match:
                raw = match.group(0)
                # Try parsing as-is first, then with repairs
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as e:
                    logger.debug("Raw JSON parse failed, attempting escape fix", error=str(e))
                # Fix unescaped newlines inside JSON string values
                fixed = re.sub(
                    r'(?<=": ")(.*?)(?="[,\n\}])',
                    lambda m: m.group(0).replace("\n", "\\n"),
                    raw,
                    flags=re.DOTALL,
                )
                return json.loads(fixed)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(
                "All JSON parse attempts failed", error=str(e), content_preview=content[:200]
            )
            raise ValueError(f"Invalid JSON response from LLM: {e}")

        raise ValueError("Invalid JSON response from LLM: no JSON object found in content")

    async def check_health(self) -> dict[str, str]:
        """
        Check health of configured LLM providers.

        Returns:
            Dict mapping provider names to status strings
        """
        status = {}
        # Health probe models per provider. These are whatever cheap/fast
        # model each provider will accept for a 1-token ping. The portkey
        # entry uses an Anthropic model because the default portkey virtual
        # key (portkeyclaude) routes to Anthropic. If you swap
        # PORTKEY_VIRTUAL_KEY to a different provider (openai-portkey, etc.),
        # update this model to match.
        all_providers = [
            ("portkey", ProviderType.PORTKEY, os.getenv(
                "PORTKEY_HEALTH_MODEL", "claude-haiku-4-5-20251001"
            )),
            ("zai", ProviderType.ZAI, "glm-4.7-flash"),
            ("openai", ProviderType.OPENAI, "gpt-4o-mini"),
            ("anthropic", ProviderType.ANTHROPIC, "claude-3-haiku-20240307"),
            ("openrouter", ProviderType.OPENROUTER, "openai/gpt-4o-mini"),
            ("google", ProviderType.GOOGLE, "gemini-2.0-flash"),
            ("mistral", ProviderType.MISTRAL, "mistral-small-latest"),
        ]

        availability_map = {
            "portkey": settings.portkey_available,
            "zai": settings.zai_available,
            "openai": settings.openai_available,
            "anthropic": settings.anthropic_available,
            "openrouter": settings.openrouter_available,
            "google": settings.google_available,
            "mistral": settings.mistral_available,
        }

        providers_to_check = [
            (name, ptype, model)
            for name, ptype, model in all_providers
            if availability_map.get(name, False)
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
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        **kwargs,
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
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        **kwargs,
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


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic LLM() constructor fix-up for generated flow code.
# ─────────────────────────────────────────────────────────────────────────────

_LLM_FIXED_BODY = (
    'LLM(\n'
    '            model=f"openai/{os.getenv(\'LLM_MODEL\', os.getenv(\'DEFAULT_MODEL\', \'claude-haiku-4-5-20251001\'))}",\n'
    '            base_url="https://api.portkey.ai/v1",\n'
    '            api_key=os.getenv("PORTKEY_API_KEY", ""),\n'
    '            extra_headers={\n'
    '                "x-portkey-api-key": os.getenv("PORTKEY_API_KEY", ""),\n'
    '                "x-portkey-virtual-key": os.getenv("PORTKEY_VIRTUAL_KEY", "portkeyclaude"),\n'
    '            },\n'
    '            temperature=0.4,\n'
    '        )'
)


def _postprocess_llm_factory(flow_code: str) -> str:
    """Replace any `LLM(...)` body with a canonical Portkey-routed factory.

    LAIAS templates + few-shot examples teach the right shape, but code-
    generation LLMs sometimes omit `extra_headers` or the `openai/` model
    prefix during long outputs. Without those fields the deployed agent
    container 401s against Portkey. This regex sweep guarantees every
    LLM() body in the generated code has the full Portkey routing block,
    regardless of what the model wrote.

    Idempotent: a body that already matches _LLM_FIXED_BODY is left alone.
    """
    import re

    # Pattern matches from `LLM(` through the matching `)` — tolerant of
    # multi-line bodies and nested parens in dict values. We use a
    # non-greedy outer match plus a simple paren-balance counter in a
    # callback to find the true end.
    idx = 0
    out = []
    while idx < len(flow_code):
        m = re.search(r'\bLLM\(', flow_code[idx:])
        if not m:
            out.append(flow_code[idx:])
            break
        start = idx + m.start()
        out.append(flow_code[idx:start])

        # Find matching close-paren
        depth = 0
        i = start + len('LLM(')  # inside the opening paren
        depth = 1
        while i < len(flow_code) and depth > 0:
            ch = flow_code[i]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            i += 1
        if depth != 0:
            # Unbalanced — bail out, don't corrupt the code
            out.append(flow_code[start:])
            break

        # Replace the entire LLM(...) body with the canonical one.
        out.append(_LLM_FIXED_BODY)
        idx = i  # resume after the replaced body

    return ''.join(out)


# ─────────────────────────────────────────────────────────────────────────────
# Runtime entrypoint injection.
# The base image `laias/agent-runner:latest` runs `python flow.py` as its CMD.
# If flow.py has no `__main__` block, the module imports then exits with
# code 0 — no crew kickoff, no artifact, no event posted to the orchestrator.
# We inject a deterministic wrapper that: (a) parses the flow class name,
# (b) instantiates it, (c) awaits kickoff_async with env-sourced inputs,
# (d) writes artifact to /app/outputs/report.md (created if missing),
# (e) POSTs a final ingest event. Failures are caught and reported.
# ─────────────────────────────────────────────────────────────────────────────

_MAIN_BLOCK_MARKER = "# ─── LAIAS runtime entrypoint (auto-injected) ───"

_MAIN_BLOCK_TEMPLATE = '''

# ─── LAIAS runtime entrypoint (auto-injected) ───
if __name__ == "__main__":
    import asyncio as _laias_asyncio
    import os as _laias_os
    import json as _laias_json
    import sys as _laias_sys
    import traceback as _laias_traceback
    from pathlib import Path as _LaiasPath
    from datetime import datetime as _laias_datetime

    try:
        import httpx as _laias_httpx
    except Exception:
        _laias_httpx = None

    _laias_out_root = _LaiasPath(_laias_os.getenv("LAIAS_OUTPUT_ROOT", "/app/outputs"))
    _laias_out_root.mkdir(parents=True, exist_ok=True)
    _laias_deployment_id = _laias_os.getenv("LAIAS_DEPLOYMENT_ID", "local")
    _laias_ingest_url = _laias_os.getenv("LAIAS_OUTPUT_INGEST_URL", "")

    def _laias_emit(kind, payload):
        event = {
            "event_type": kind,
            "deployment_id": _laias_deployment_id,
            "timestamp": _laias_datetime.utcnow().isoformat() + "Z",
            "payload": payload,
        }
        # Always write to the file channel — guaranteed surface for the portal.
        (_laias_out_root / "events.ndjson").open("a", encoding="utf-8").write(
            _laias_json.dumps(event) + "\\n"
        )
        if _laias_httpx is not None and _laias_ingest_url:
            try:
                _laias_httpx.post(_laias_ingest_url, json=event, timeout=5.0)
            except Exception:
                # Best-effort: ingest is optional, file channel is authoritative.
                pass

    # Auto-discover the Flow subclass AND its state type.
    _laias_flow_cls = None
    _laias_state_cls = None
    try:
        from crewai.flow.flow import Flow as _LaiasFlowBase
    except Exception:
        _LaiasFlowBase = None
    try:
        from pydantic import BaseModel as _LaiasBaseModel
    except Exception:
        _LaiasBaseModel = None
    for _laias_name, _laias_obj in list(globals().items()):
        if not isinstance(_laias_obj, type) or _laias_name == "Flow":
            continue
        if _LaiasFlowBase is not None:
            try:
                if issubclass(_laias_obj, _LaiasFlowBase):
                    _laias_flow_cls = _laias_obj
                    # Try the generic-param path first: `Flow[StateCls]`.
                    for _ob in getattr(_laias_obj, "__orig_bases__", ()):
                        args = getattr(_ob, "__args__", None)
                        if not args:
                            continue
                        cand = args[0]
                        # Skip TypeVars / ForwardRefs — we want a real class.
                        if isinstance(cand, type) and _LaiasBaseModel is not None and issubclass(cand, _LaiasBaseModel):
                            _laias_state_cls = cand
                            break
                    break
            except Exception:
                pass
    if _laias_flow_cls is None:
        for _laias_name, _laias_obj in list(globals().items()):
            if isinstance(_laias_obj, type) and hasattr(_laias_obj, "kickoff_async"):
                _laias_flow_cls = _laias_obj
                break
    # Fallback state-class discovery: if the generic-param path yielded a
    # TypeVar or nothing, scan the module for the first BaseModel subclass
    # named like `*State*`. This catches the conventional
    # `class TrafficTattletaleState(BaseModel)` pattern the generator emits.
    if _laias_state_cls is None and _LaiasBaseModel is not None:
        for _laias_name, _laias_obj in list(globals().items()):
            if (
                isinstance(_laias_obj, type)
                and _laias_obj is not _LaiasBaseModel
                and "State" in _laias_name
            ):
                try:
                    if issubclass(_laias_obj, _LaiasBaseModel):
                        _laias_state_cls = _laias_obj
                        break
                except Exception:
                    pass

    # Tenant configuration comes from upper-case env vars that aren't in
    # the platform allow-list. These become state fields if (and only if)
    # the Flow has a typed state class; otherwise CrewAI stores them as a
    # plain dict, which breaks `self.state.<field>` access inside flow
    # methods. The Pydantic construction below tolerates extra keys.
    _laias_tenant_env = {
        k.lower(): v
        for k, v in _laias_os.environ.items()
        if k.isupper() and not k.startswith(
            ("PATH", "HOME", "PYTHON", "LAIAS_", "PORTKEY_", "OPENAI_",
             "ANTHROPIC_", "LC_", "LANG", "GPG_", "SHELL", "TERM", "USER",
             "HOSTNAME", "MEMORY_", "TOKENIZERS_", "VERBOSE", "LOG_", "TIKTOKEN_")
        )
    }

    async def _laias_run():
        if _laias_flow_cls is None:
            raise RuntimeError("No Flow subclass found in module — nothing to kick off.")
        # CrewAI Flow[T].__init__() constructs a default-populated typed
        # state. We must NOT pass `inputs=` to kickoff — that silently
        # replaces the typed state with a plain dict and breaks every
        # `self.state.<field>` access downstream. Instead: build the flow
        # first, then mutate fields on the already-constructed typed
        # state before kickoff reads them.
        flow = _laias_flow_cls()
        _laias_emit("state_seeding_start", {
            "state_cls": _laias_state_cls.__name__ if _laias_state_cls else None,
            "env_keys_available": sorted(_laias_tenant_env.keys()),
        })
        _laias_seeded = []
        _laias_failed = []
        if _laias_state_cls is not None:
            try:
                _known = set(getattr(_laias_state_cls, "model_fields", {}).keys())
                for k, v in _laias_tenant_env.items():
                    if k in _known:
                        try:
                            setattr(flow.state, k, v)
                            _laias_seeded.append({"field": k, "value_chars": len(str(v))})
                        except Exception as _laias_seed_err:
                            _laias_failed.append({"field": k, "error": str(_laias_seed_err)})
            except Exception as _laias_outer_err:
                _laias_failed.append({"error": str(_laias_outer_err)})
        _laias_emit("state_seeding_done", {
            "state_fields": sorted(getattr(_laias_state_cls, "model_fields", {}).keys()) if _laias_state_cls else [],
            "seeded": _laias_seeded,
            "failed": _laias_failed,
            "post_seed_site_url": str(getattr(flow.state, "site_url", "<unset>")),
        })
        kickoff = getattr(flow, "kickoff_async", None) or getattr(flow, "kickoff", None)
        if kickoff is None:
            raise RuntimeError(f"Flow {_laias_flow_cls.__name__} has no kickoff method.")
        if _laias_asyncio.iscoroutinefunction(kickoff):
            return await kickoff()
        return kickoff()

    _laias_emit("flow_starting", {"inputs": list(_laias_tenant_env.keys())})
    try:
        _laias_result = _laias_asyncio.run(_laias_run())
        # Extract the actual Markdown report from the flow's final state.
        # Flow.kickoff_async returns the state dict/object; the generated
        # code typically stores the report in one of a few conventional
        # fields. Fall back to str(result) only if none exist.
        def _laias_extract_report(r):
            if r is None:
                return ""
            for field in (
                "report_content", "final_report", "report", "output",
                "markdown", "content", "summary", "result",
            ):
                try:
                    v = getattr(r, field, None) if not isinstance(r, dict) else r.get(field)
                except Exception:
                    v = None
                if isinstance(v, str) and v.strip():
                    return v
            # Last resort: repr the whole state
            return str(r)

        _laias_text = _laias_extract_report(_laias_result)
        (_laias_out_root / "report.md").write_text(_laias_text, encoding="utf-8")
        # Also dump the full state for debugging/audit.
        try:
            _laias_state_repr = (
                _laias_result.model_dump()
                if hasattr(_laias_result, "model_dump")
                else dict(_laias_result) if isinstance(_laias_result, dict)
                else {"repr": str(_laias_result)}
            )
            (_laias_out_root / "final_state.json").write_text(
                _laias_json.dumps(_laias_state_repr, default=str, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        _laias_emit("flow_completed", {"report_bytes": len(_laias_text)})
        _laias_sys.exit(0)
    except Exception as _laias_err:
        _laias_tb = _laias_traceback.format_exc()
        (_laias_out_root / "error.txt").write_text(_laias_tb, encoding="utf-8")
        _laias_emit("flow_failed", {"error": str(_laias_err), "traceback_bytes": len(_laias_tb)})
        _laias_sys.exit(1)
'''


def _postprocess_ensure_main(flow_code: str) -> str:
    """Append a deterministic __main__ runtime block if none exists.

    The agent-runner Dockerfile runs `python flow.py`. Without a __main__
    block the module just imports and exits with no side effects — no crew
    kickoff, no artifact. This injection guarantees runtime execution,
    error capture, and event emission regardless of what the code
    generator produced.

    Idempotent — the marker comment prevents double-injection.
    """
    if _MAIN_BLOCK_MARKER in flow_code:
        return flow_code
    # If generator produced its own __main__ block, wrap/augment rather
    # than replace: append ours unconditionally so there's always a
    # guaranteed path. Python executes all top-level code in order; an
    # existing __main__ that already exited will short-circuit ours (via
    # sys.exit), and one that completed without exit will fall through to
    # ours, which re-runs kickoff if needed.
    return flow_code.rstrip() + "\n" + _MAIN_BLOCK_TEMPLATE


_STATE_ASSIGNMENT_PATTERN = (
    r"^(\s*)self\.state\s*=\s*[A-Za-z_][A-Za-z0-9_]*\([^)]*\)\s*(?:#[^\n]*)?$"
)


def _postprocess_strip_state_assignment(flow_code: str) -> str:
    """Remove `self.state = SomeState()` assignments inside __init__.

    CrewAI `Flow[T]` exposes `self.state` as a read-only managed property;
    direct assignment raises `AttributeError: property 'state' has no setter`
    at runtime. Generator models frequently write this line anyway because
    it reads like idiomatic Python. We strip it deterministically — the
    state is already initialised by the Flow base class via the generic
    type argument, and any initial values should come through
    `kickoff_async(inputs=...)` instead.
    """
    import re

    cleaned_lines: list[str] = []
    for line in flow_code.splitlines():
        if re.match(_STATE_ASSIGNMENT_PATTERN, line):
            # Keep a short comment so the change is traceable during audit.
            indent = re.match(r"^(\s*)", line).group(1)
            cleaned_lines.append(
                f"{indent}# [laias-postprocess] removed 'self.state = …()' — "
                "Flow[T].state is a managed property."
            )
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


_SAFE_IMPORT_MARKER = "# ─── LAIAS safe-import shim (auto-injected) ───"

_SAFE_IMPORT_PREAMBLE = '''# ─── LAIAS safe-import shim (auto-injected) ───
# Code-generation LLMs often import symbols that don\'t exist in the
# runtime\'s crewai_tools version (FileWriteTool, FileReadTool, etc.).
# A failed top-level import prevents our main-block entrypoint from
# even running, so no error artifact is written. We patch the import
# machinery here: if a submodule or symbol is missing, substitute a
# no-op stub that the generated code can reference harmlessly, and
# log the substitution to the events file so the portal can surface it.
import builtins as _laias_builtins
import os as _laias_os_early
import sys as _laias_sys_early
import json as _laias_json_early
from pathlib import Path as _LaiasPathEarly
from datetime import datetime as _laias_dt_early

_laias_early_out = _LaiasPathEarly(_laias_os_early.getenv("LAIAS_OUTPUT_ROOT", "/app/outputs"))
try:
    _laias_early_out.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


def _laias_stub_callable(*_args, **_kwargs):
    return (
        "[laias-stub] This tool is unavailable at runtime (shimmed by "
        "LAIAS safe-import). The generated code referenced a tool that the "
        "installed crewai_tools version does not export. Returning an "
        "empty result so the flow can continue."
    )


# Create a BaseTool-compatible stub. crewai.tools.BaseTool extends Pydantic;
# agents validate every entry in their `tools` list against that type, so a
# plain class will fail with 'Input should be a valid BaseTool'. We subclass
# the real BaseTool if importable; if not, we fall back to a minimal shim.
try:
    from crewai.tools import BaseTool as _LaiasRealBaseTool
    class _LaiasStubTool(_LaiasRealBaseTool):
        name: str = "laias-stub"
        description: str = "LAIAS safe-import stub — no-op."
        def _run(self, *_args, **_kwargs):
            return _laias_stub_callable()
except Exception:
    class _LaiasStubTool:  # pragma: no cover
        name = "laias-stub"
        description = "LAIAS safe-import stub — no-op (minimal)."
        def __init__(self, *_args, **_kwargs):
            pass
        def __call__(self, *_args, **_kwargs):
            return _laias_stub_callable()
        def _run(self, *_args, **_kwargs):
            return _laias_stub_callable()
        def run(self, *_args, **_kwargs):
            return _laias_stub_callable()


_laias_original_import = _laias_builtins.__import__


def _laias_safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    try:
        mod = _laias_original_import(name, globals, locals, fromlist, level)
    except ImportError as exc:
        # If the missing module is crewai_tools or a submodule thereof,
        # return a stub module carrying _LaiasStubTool for every name.
        if name == "crewai_tools" or name.startswith("crewai_tools."):
            import types as _laias_types
            stub = _laias_types.ModuleType(name)
            for sym in (fromlist or ()):
                setattr(stub, sym, _LaiasStubTool)
            try:
                (_laias_early_out / "events.ndjson").open("a", encoding="utf-8").write(
                    _laias_json_early.dumps({
                        "event_type": "safe_import_stubbed",
                        "timestamp": _laias_dt_early.utcnow().isoformat() + "Z",
                        "payload": {"module": name, "fromlist": list(fromlist or ()), "error": str(exc)},
                    }) + "\\n"
                )
            except Exception:
                pass
            return stub
        raise

    # Module imported successfully, but some `from x import Y` symbols may
    # be missing. Patch those too.
    if fromlist and name.startswith("crewai_tools"):
        for sym in fromlist:
            if not hasattr(mod, sym):
                setattr(mod, sym, _LaiasStubTool)
                try:
                    (_laias_early_out / "events.ndjson").open("a", encoding="utf-8").write(
                        _laias_json_early.dumps({
                            "event_type": "safe_import_symbol_stubbed",
                            "timestamp": _laias_dt_early.utcnow().isoformat() + "Z",
                            "payload": {"module": name, "symbol": sym},
                        }) + "\\n"
                    )
                except Exception:
                    pass
    return mod


_laias_builtins.__import__ = _laias_safe_import
# ─── end safe-import shim ───

'''


def _postprocess_ensure_safe_imports(flow_code: str) -> str:
    """Prepend the safe-import shim if not already present.

    The shim MUST come before the first `from crewai_tools import …` line
    in the generated code, otherwise the patched __import__ never gets a
    chance. Because we prepend, all subsequent imports go through the
    shimmed machinery and missing crewai_tools symbols become harmless
    stubs instead of module-load-time ImportErrors.
    """
    if _SAFE_IMPORT_MARKER in flow_code:
        return flow_code
    return _SAFE_IMPORT_PREAMBLE + flow_code


def _postprocess_strip_inputs_param(flow_code: str) -> str:
    """Remove the `inputs:` positional parameter from @start-decorated methods.

    CrewAI's `@start()` calls the decorated method with NO arguments —
    inputs live on `self.state`, which CrewAI pre-populates from the
    `kickoff_async(inputs={...})` dict. Generator models frequently write

        @start()
        async def initialize(self, inputs: Dict[str, Any]) -> Something:
            self.state.foo = inputs.get("foo", "")

    which raises `TypeError: initialize() missing 1 required positional
    argument: 'inputs'`. We rewrite the signature to `(self)` only and
    translate body references `inputs.get("x", default)` /
    `inputs["x"]` → `getattr(self.state, "x", default)` /
    `getattr(self.state, "x")` so the body still compiles.

    We deliberately do NOT touch `@listen`/`@router` methods — those DO
    receive the return value of the listened method as a positional arg.
    """
    import re

    lines = flow_code.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    rewrote_method_indent: str | None = None

    def _balance_match_paren(s: str, start: int) -> int:
        """Return index of matching close-paren for open paren at `start`."""
        depth = 1
        i2 = start + 1
        while i2 < len(s) and depth > 0:
            if s[i2] == "(":
                depth += 1
            elif s[i2] == ")":
                depth -= 1
            i2 += 1
        return i2 - 1 if depth == 0 else -1

    while i < len(lines):
        line = lines[i]

        # Is this an @start() decorator?
        dec_match = re.match(r"^(\s*)@start\b", line)
        if dec_match:
            out.append(line)
            # Skip any additional stacked decorators
            j = i + 1
            while j < len(lines) and re.match(r"^\s*@", lines[j]):
                out.append(lines[j])
                j += 1
            if j >= len(lines):
                i = j
                continue
            def_line = lines[j]
            # Does the def line have inputs as 2nd param?
            m = re.match(
                r"^(?P<indent>\s*)(?P<async>async\s+)?def\s+(?P<name>[A-Za-z_]\w*)\s*\(\s*self\s*,\s*inputs\b",
                def_line,
            )
            if m:
                indent = m.group("indent")
                is_async = m.group("async") or ""
                name = m.group("name")
                # Find the closing paren of the signature (could span lines)
                signature_text = def_line[m.start():]
                paren_open = signature_text.index("(")
                # Concatenate following lines until we find a balanced close
                buffer = signature_text
                buffer_start_line = j
                while True:
                    close_idx = _balance_match_paren(buffer, paren_open)
                    if close_idx != -1:
                        break
                    buffer_start_line += 1
                    if buffer_start_line >= len(lines):
                        close_idx = -1
                        break
                    buffer += lines[buffer_start_line]
                if close_idx == -1:
                    # Can't safely rewrite; keep as-is
                    out.append(def_line)
                    i = j + 1
                    continue
                # Everything after close_idx until the colon/end-of-line is the return type
                after_paren = buffer[close_idx + 1 :]
                colon_idx = after_paren.index(":") if ":" in after_paren else -1
                rettype = after_paren[:colon_idx].rstrip() if colon_idx != -1 else ""
                rewritten = (
                    f"{indent}{is_async}def {name}(self){rettype}:"
                    "  # [laias-postprocess] @start() removes inputs param\n"
                )
                out.append(rewritten)
                # Skip the consumed def lines
                i = buffer_start_line + 1
                rewrote_method_indent = indent
                continue
            else:
                out.append(def_line)
                i = j + 1
                continue

        # In the body of a rewritten method, translate inputs refs.
        if rewrote_method_indent is not None:
            stripped = line.lstrip()
            if stripped and not line.startswith(rewrote_method_indent + " ") and not line.startswith(
                rewrote_method_indent + "\t"
            ) and not re.match(r"^\s*$", line):
                rewrote_method_indent = None
            else:
                line = re.sub(
                    r"\binputs\.get\(\s*(['\"])([^'\"]+)\1\s*(?:,\s*([^)]+))?\)",
                    lambda m: (
                        f'getattr(self.state, "{m.group(2)}", {m.group(3).strip()})'
                        if m.group(3)
                        else f'getattr(self.state, "{m.group(2)}", None)'
                    ),
                    line,
                )
                line = re.sub(
                    r"\binputs\[\s*(['\"])([^'\"]+)\1\s*\]",
                    lambda m: f'getattr(self.state, "{m.group(2)}")',
                    line,
                )

        out.append(line)
        i += 1

    return "".join(out)


def _postprocess_fix_multiline_fstrings(flow_code: str) -> str:
    """Convert `f"...<newline>..."` → `f\"\"\"...<newline>...\"\"\"`.

    LLMs frequently emit Task descriptions like

        description=f"Analyze traffic for website: {x}
        - point 1
        - point 2",

    Python rejects that with `SyntaxError: unterminated string literal`
    because single-quoted f-strings must be on one line. We detect
    a single-or-double-quoted f-string that contains a raw newline
    before its matching close quote and upgrade it to a triple-quoted
    f-string. Idempotent — triple-quoted strings are untouched.
    """
    import re

    def walk(s: str, i: int) -> str:
        out: list[str] = []
        while i < len(s):
            # Look for the start of an f-string with a SINGLE quote char
            m = re.match(r'([fF][rR]?|[rR][fF])(["\'])', s[i:])
            if not m:
                out.append(s[i])
                i += 1
                continue
            prefix = m.group(1)
            quote = m.group(2)
            # Already triple-quoted? Pass through as-is
            if s[i + len(prefix): i + len(prefix) + 3] == quote * 3:
                out.append(s[i])
                i += 1
                continue

            # Find the matching close-quote on the same line
            j = i + len(prefix) + 1
            has_newline = False
            while j < len(s):
                ch = s[j]
                if ch == "\\" and j + 1 < len(s):
                    j += 2
                    continue
                if ch == "\n":
                    has_newline = True
                    j += 1
                    continue
                if ch == quote:
                    break
                j += 1

            if has_newline and j < len(s) and s[j] == quote:
                # Rewrite to triple-quoted f-string
                body = s[i + len(prefix) + 1 : j]
                out.append(f"{prefix}{quote*3}{body}{quote*3}")
                i = j + 1
            else:
                # Copy the whole (single-line) string verbatim
                end = j + 1 if j < len(s) else j
                out.append(s[i:end])
                i = end
        return "".join(out)

    return walk(flow_code, 0)


def _postprocess_flow_code(flow_code: str) -> str:
    """Full deterministic pipeline applied in-order to the generator output.

    Each step is idempotent and fixes a specific class of LLM hallucination
    that would otherwise crash the deployed container. Ordering matters:
    the safe-import shim goes first (must precede any `from x import y`)
    and the runtime entrypoint goes last (must be at module bottom). The
    f-string fix comes before structural rewrites so subsequent regex
    passes see valid single-line string literals.
    """
    fixed = _postprocess_fix_multiline_fstrings(flow_code)
    fixed = _postprocess_ensure_safe_imports(fixed)
    fixed = _postprocess_llm_factory(fixed)
    fixed = _postprocess_strip_state_assignment(fixed)
    fixed = _postprocess_strip_inputs_param(fixed)
    fixed = _postprocess_ensure_main(fixed)
    return fixed


# Global service instance
_llm_service: LLMService | None = None


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

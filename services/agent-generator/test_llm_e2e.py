#!/usr/bin/env python3
"""
E2E Test Script for LLM Provider Integration.
Tests multiple providers: ZAI, OpenAI, Anthropic.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_provider import (
    LLMProvider,
    LLMConfig,
    ProviderType,
)


async def test_provider(provider_type: ProviderType, model: str, api_key: str) -> dict:
    """Test a single LLM provider."""
    print(f"\n{'='*60}")
    print(f"Testing: {provider_type.value.upper()} / {model}")
    print(f"{'='*60}")

    if not api_key:
        print(f"  [SKIP] No API key found for {provider_type.value}")
        return {"provider": provider_type.value, "status": "skipped", "reason": "no_api_key"}

    try:
        config = LLMConfig(
            provider=provider_type,
            model=model,
            max_tokens=50,
            timeout=30,
        )
        config.api_key = api_key  # Set directly

        async with LLMProvider(config) as llm:
            response = await llm.complete([
                {"role": "user", "content": "Say 'Hello from LAIAS' and nothing else."}
            ])

        print(f"  [OK] Response: {response.content[:100]}...")
        print(f"  [OK] Tokens: {response.tokens_used}")
        return {
            "provider": provider_type.value,
            "status": "success",
            "tokens": response.tokens_used,
            "response_preview": response.content[:50]
        }

    except Exception as e:
        print(f"  [ERROR] {str(e)[:200]}")
        return {"provider": provider_type.value, "status": "error", "error": str(e)[:200]}


async def main():
    """Run all provider tests."""
    print("\n" + "="*60)
    print("LAIAS LLM Provider E2E Tests")
    print("="*60)

    # Check available API keys
    zai_key = os.getenv("ZAI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    portkey_key = os.getenv("PORTKEY_API_KEY", "")

    print(f"\nAPI Keys Status:")
    print(f"  ZAI:       {'[SET]' if zai_key else '[NOT SET]'}")
    print(f"  PORTKEY:   {'[SET]' if portkey_key else '[NOT SET]'}")
    print(f"  OPENAI:    {'[SET]' if openai_key else '[NOT SET]'}")
    print(f"  ANTHROPIC: {'[SET]' if anthropic_key else '[NOT SET]'}")

    results = []

    # Test ZAI (GLM-5)
    if zai_key:
        results.append(await test_provider(
            ProviderType.ZAI, "glm-5", zai_key
        ))

    # Test OpenAI
    if openai_key:
        results.append(await test_provider(
            ProviderType.OPENAI, "gpt-4o-mini", openai_key
        ))

    # Test Anthropic
    if anthropic_key:
        results.append(await test_provider(
            ProviderType.ANTHROPIC, "claude-3-haiku-20240307", anthropic_key
        ))

    # Test Portkey (if key available)
    if portkey_key:
        results.append(await test_provider(
            ProviderType.PORTKEY, "@zhipu/glm-4.7-flashx", portkey_key
        ))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")

    for r in results:
        status_icon = "[OK]" if r["status"] == "success" else "[SKIP]" if r["status"] == "skipped" else "[ERR]"
        print(f"  {status_icon} {r['provider']}: {r['status']}")

    print(f"\nTotal: {success} passed, {skipped} skipped, {errors} failed")

    return errors == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

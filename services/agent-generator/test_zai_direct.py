#!/usr/bin/env python3
"""Test ZAI with thinking disabled via LLMProvider."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv(Path(__file__).parent / ".env")

from app.services.llm_provider import LLMProvider, LLMConfig, ProviderType

async def test_zai():
    print("Testing ZAI with LLMProvider (thinking disabled)...")

    config = LLMConfig(
        provider=ProviderType.ZAI,
        model="glm-5",
        max_tokens=50,
        timeout=30,
    )
    config.api_key = os.getenv("ZAI_API_KEY")

    async with LLMProvider(config) as llm:
        response = await llm.complete([
            {"role": "user", "content": "Say 'Hello from LAIAS' and nothing else."}
        ])

    print(f"Status: SUCCESS")
    print(f"Content: {response.content}")
    print(f"Tokens: {response.tokens_used}")
    return response.content

if __name__ == "__main__":
    asyncio.run(test_zai())

#!/usr/bin/env python3
"""
Quick runner for Legacy Research Workflow.

Usage:
    python agents/run_research.py "your research topic here"

Environment:
    Uses LAIAS agent-generator venv with CrewAI
    Reads ZAI_API_KEY from /Volumes/Storage/LAIAS/.env
    Outputs to /Volumes/Storage/Research/
"""

import sys
import os
import asyncio
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/Volumes/Storage/LAIAS/.env')

# Import the workflow
from legacy_research_workflow import LegacyResearchWorkflow


async def run_research(topic: str):
    """Run research workflow on the given topic."""

    if not topic or not topic.strip():
        print("❌ Error: Research topic cannot be empty")
        print("\nUsage: python agents/run_research.py \"your research topic here\"")
        sys.exit(1)

    print("="*70)
    print("🔬 LEGACY AI RESEARCH WORKFLOW")
    print("="*70)
    print(f"Topic: {topic}")
    print(f"LLM Provider: {os.getenv('LAIAS_LLM_PROVIDER', 'zai')}")
    print(f"Output: /Volumes/Storage/Research/")
    print("="*70)
    print()

    # Set environment variable for the workflow
    os.environ['RESEARCH_TOPIC'] = topic

    # Initialize and run workflow
    workflow = LegacyResearchWorkflow()

    inputs = {
        "topic": topic,
        "output_directory": "/Volumes/Storage/Research"
    }

    print("🚀 Starting research workflow...\n")

    result = await workflow.kickoff_async(inputs=inputs)

    # Print results
    print("\n" + "="*70)
    print("✅ RESEARCH WORKFLOW COMPLETE")
    print("="*70)
    print(f"Status: {workflow.state.status}")
    print(f"Progress: {workflow.state.progress}%")
    print(f"Task ID: {workflow.state.task_id}")

    if workflow.state.documentation_path:
        print(f"\n📄 Documentation: {workflow.state.documentation_path}")
        print(f"   Created: {workflow.state.completed_at}")

    if workflow.state.generated_workflow:
        print(f"\n🤖 Generated Workflow: Yes")

    if workflow.state.error_count > 0:
        print(f"\n⚠️  Errors encountered: {workflow.state.error_count}")
        if workflow.state.last_error:
            print(f"   Last error: {workflow.state.last_error}")

    print("="*70)

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agents/run_research.py \"your research topic here\"")
        print("\nExamples:")
        print("  python agents/run_research.py \"Best practices for LinkedIn posting times\"")
        print("  python agents/run_research.py \"AI agent framework comparison 2026\"")
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    asyncio.run(run_research(topic))

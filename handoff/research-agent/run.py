#!/usr/bin/env python3
"""
================================================================================
            RESEARCH AGENT CLI
================================================================================

A simple command-line interface for running the research workflow.

Usage:
    python run.py "Your research topic"
    python run.py --config custom_config.yaml "Your topic"
    python run.py --topic-file topics.txt
    RESEARCH_TOPIC="Your topic" python run.py

================================================================================
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from research_workflow import ResearchWorkflow, load_config


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the Research Agent workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run.py "Best practices for email marketing"
    python run.py --output ./my_research "Competitor analysis for SaaS"
    python run.py --config prod.yaml "Market trends 2024"
        """
    )
    
    parser.add_argument(
        "topic",
        nargs="?",
        help="The research topic to investigate"
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output directory for research documents"
    )
    
    parser.add_argument(
        "--topic-file", "-f",
        help="File containing research topics (one per line)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


async def run_research(topic: str, config_path: str, output_dir: str = None):
    """Run a single research workflow."""
    
    # Load config
    config = load_config()
    if os.path.exists(config_path):
        import yaml
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                config.update(yaml_config)
    
    # Override output directory if specified
    if output_dir:
        config["output_directory"] = output_dir
    
    # Create and run workflow
    workflow = ResearchWorkflow(config=config)
    
    inputs = {"topic": topic}
    
    print(f"\n{'='*60}")
    print(f"RESEARCH AGENT")
    print(f"{'='*60}")
    print(f"Topic: {topic}")
    print(f"Output: {config.get('output_directory', './research_output')}")
    print(f"{'='*60}\n")
    
    result = await workflow.kickoff_async(inputs=inputs)
    
    print(f"\n{'='*60}")
    print("RESEARCH WORKFLOW COMPLETE")
    print(f"{'='*60}")
    print(f"Status: {workflow.state.status}")
    print(f"Progress: {workflow.state.progress}%")
    print(f"Documentation: {workflow.state.documentation_path}")
    if workflow.state.generated_actions:
        print(f"Actions Generated: Yes")
    if workflow.state.last_error:
        print(f"Last Error: {workflow.state.last_error}")
    print(f"{'='*60}\n")
    
    return workflow.state


async def main():
    """Main entry point."""
    args = parse_args()
    
    # Get topics to research
    topics = []
    
    # From command line argument
    if args.topic:
        topics.append(args.topic)
    
    # From environment variable
    env_topic = os.getenv("RESEARCH_TOPIC")
    if env_topic and env_topic not in topics:
        topics.append(env_topic)
    
    # From file
    if args.topic_file:
        with open(args.topic_file, 'r') as f:
            file_topics = [line.strip() for line in f if line.strip()]
            topics.extend(file_topics)
    
    # Prompt if no topics
    if not topics:
        topic = input("Enter your research topic: ")
        if not topic:
            print("No topic provided. Exiting.")
            sys.exit(1)
        topics.append(topic)
    
    # Run research for each topic
    for topic in topics:
        try:
            await run_research(
                topic=topic,
                config_path=args.config,
                output_dir=args.output
            )
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            sys.exit(130)
        except Exception as e:
            print(f"\nError running research: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

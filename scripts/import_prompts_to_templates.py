#!/usr/bin/env python3
"""
Import prompts from Prompt Library to LAIAS templates.

Converts markdown agent prompts to YAML template format.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional


# Paths
PROMPT_LIBRARY = Path("/Volumes/Storage/Prompt Library")
AUTONOMOUS_AGENTS = PROMPT_LIBRARY / "agents" / "autonomous"
LEGACY_AGENTS = PROMPT_LIBRARY / "agents" / "legacyai"
NOTION_AGENTS = PROMPT_LIBRARY / "agents-refactored" / "agents" / "notion"
CREWAI_AGENTS = PROMPT_LIBRARY / "agents-refactored" / "crewai-methodology"
MIDDLE_AMERICA_AGENTS = PROMPT_LIBRARY / "agents-refactored" / "middle-america-automation"
INDUSTRY_AGENTS = PROMPT_LIBRARY / "agents-refactored" / "industry-standards-2027" / "examples"
TEMPLATES_OUTPUT = Path("/Volumes/Storage/LAIAS/templates/presets")

# Category mapping
CATEGORY_MAP = {
    "research": "research",
    "analysis": "analysis",
    "development": "development",
    "code": "development",
    "testing": "development",
    "security": "security",
    "documentation": "content",
    "content": "content",
    "support": "support",
    "automation": "productivity",
    "orchestrat": "management",
    "manager": "management",
    "marketing": "marketing",
    "default": "productivity"
}

# Tool mapping based on keywords
TOOL_MAP = {
    "web": ["SerperDevTool", "ScrapeWebsiteTool"],
    "research": ["SerperDevTool", "ScrapeWebsiteTool"],
    "scrape": ["ScrapeWebsiteTool"],
    "code": ["FileReadTool", "CodeInterpreterTool"],
    "file": ["FileReadTool", "DirectoryReadTool"],
    "database": ["MySQLTool", "PostgresTool"],
    "api": ["APIRequestTool"],
    "test": ["CodeInterpreterTool", "FileReadTool"],
    "document": ["FileReadTool", "PDFSearchTool"],
    "analysis": ["FileReadTool", "CodeInterpreterTool"],
    "security": ["SerperDevTool", "FileReadTool"],
    "default": ["SerperDevTool", "FileReadTool"]
}


def detect_category(content: str, filename: str) -> str:
    """Detect category from content and filename."""
    content_lower = content.lower()
    filename_lower = filename.lower()

    # Check filename first
    for keyword, category in CATEGORY_MAP.items():
        if keyword in filename_lower:
            return category

    # Check content
    for keyword, category in CATEGORY_MAP.items():
        if keyword in content_lower:
            return category

    return CATEGORY_MAP["default"]


def detect_tools(content: str) -> List[str]:
    """Detect appropriate tools from content."""
    content_lower = content.lower()
    tools = set()

    for keyword, tool_list in TOOL_MAP.items():
        if keyword in content_lower:
            for tool in tool_list:
                tools.add(tool)

    if not tools:
        tools.update(TOOL_MAP["default"])

    return list(tools)[:4]  # Max 4 tools


def extract_name(content: str, filename: str) -> str:
    """Extract agent name from content or filename."""
    # Try to find title in content
    lines = content.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if line.startswith('# '):
            name = line[2:].strip()
            # Clean up name
            name = re.sub(r'\s+Agent$', '', name, flags=re.I)
            name = re.sub(r'_', ' ', name)
            return name.title()

    # Fallback to filename
    name = filename.replace('-agent', '').replace('_', ' ')
    return name.title()


def extract_description(content: str) -> str:
    """Extract description from content."""
    lines = content.split('\n')
    description_lines = []
    in_description = False

    for line in lines[1:20]:  # Skip title, look at first 20 lines
        line = line.strip()

        if not line:
            if in_description and description_lines:
                break
            continue

        # Skip headers and dividers
        if line.startswith('#') or line.startswith('---'):
            if in_description and description_lines:
                break
            continue

        # Look for description after title
        if not in_description and len(line) > 20:
            in_description = True

        if in_description:
            description_lines.append(line)
            if len(' '.join(description_lines)) > 200:
                break

    description = ' '.join(description_lines)
    # Truncate to reasonable length
    if len(description) > 250:
        description = description[:247] + '...'

    # ALWAYS return a valid string, never None
    return description.strip() if description.strip() else "A specialized agent for autonomous task execution."


def extract_tags(content: str, filename: str) -> List[str]:
    """Extract tags from content."""
    tags = set()

    # From filename
    parts = filename.replace('-agent', '').split('-')
    for part in parts:
        if len(part) > 3:
            tags.add(part.lower())

    # From content keywords
    keywords = [
        'research', 'analysis', 'code', 'development', 'testing',
        'security', 'automation', 'orchestration', 'documentation',
        'api', 'web', 'database', 'refactoring', 'monitoring'
    ]

    content_lower = content.lower()
    for kw in keywords:
        if kw in content_lower:
            tags.add(kw)

    return list(tags)[:5]


def extract_sample_prompts(content: str) -> List[str]:
    """Extract sample prompts from content."""
    prompts = []

    # Look for "when to invoke" sections
    invoke_section = re.search(
        r'##\s*When to Invoke.*?\n([\s\S]*?)(?=\n##|\Z)',
        content,
        re.I
    )

    if invoke_section:
        section_text = invoke_section.group(1)
        # Extract bullet points
        bullets = re.findall(r'[-*]\s*(.+)', section_text)
        for bullet in bullets[:3]:
            if len(bullet) > 20:
                prompts.append(bullet.strip())

    # ALWAYS return a valid list, never None or empty
    return prompts[:3] if prompts else ["Run this agent for specialized task execution."]


def convert_md_to_yaml(md_path: Path) -> Optional[Dict]:
    """Convert a markdown prompt file to YAML template structure."""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip index files
        if md_path.name.lower() in ['index.md', 'readme.md']:
            return None

        filename = md_path.stem

        # Extract components
        name = extract_name(content, filename)
        description = extract_description(content)
        category = detect_category(content, filename)
        tools = detect_tools(content)
        tags = extract_tags(content, filename)
        sample_prompts = extract_sample_prompts(content)

        # Determine complexity
        complexity = "moderate"
        if any(w in content.lower() for w in ['simple', 'basic', 'single']):
            complexity = "simple"
        elif any(w in content.lower() for w in ['complex', 'advanced', 'multi-agent', 'orchestrat']):
            complexity = "complex"

        # Create template structure
        template = {
            'id': filename.replace('-', '_'),
            'name': name,
            'description': description,
            'category': category,
            'tags': tags,
            'default_complexity': complexity,
            'default_tools': tools,
            'sample_prompts': sample_prompts,
            'suggested_config': {
                'llm_provider': 'openai',
                'model': 'gpt-4o',
                'include_memory': True,
                'max_agents': 3 if complexity == "moderate" else (1 if complexity == "simple" else 5)
            },
            'agent_structure': {
                'agents': [
                    {
                        'name': 'primary_agent',
                        'role': f"{name} specialist",
                        'backstory': f"Expert {name.lower()} with deep domain knowledge."
                    }
                ]
            },
            'expected_outputs': [
                'Task completion report',
                'Analysis summary',
                'Recommendations'
            ]
        }

        return template

    except Exception as e:
        print(f"Error processing {md_path}: {e}")
        return None


def main():
    """Main import function."""
    print("=" * 60)
    print("LAIAS Template Importer")
    print("=" * 60)

    # Ensure output directory exists
    TEMPLATES_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Collect all markdown files
    md_files = []

    # Autonomous agents
    if AUTONOMOUS_AGENTS.exists():
        md_files.extend(AUTONOMOUS_AGENTS.glob("*.md"))
        print(f"Found {len(list(AUTONOMOUS_AGENTS.glob('*.md')))} autonomous agent prompts")

    # Legacy agents
    if LEGACY_AGENTS.exists():
        md_files.extend(LEGACY_AGENTS.glob("*.md"))
        print(f"Found {len(list(LEGACY_AGENTS.glob('*.md')))} legacy agent prompts")

    # Notion agents
    if NOTION_AGENTS.exists():
        md_files.extend(NOTION_AGENTS.glob("*.md"))
        print(f"Found {len(list(NOTION_AGENTS.glob('*.md')))} notion agent prompts")

    # CrewAI methodology agents
    if CREWAI_AGENTS.exists():
        md_files.extend(CREWAI_AGENTS.glob("*.md"))
        print(f"Found {len(list(CREWAI_AGENTS.glob('*.md')))} crewai methodology prompts")

    # Middle America automation agents
    if MIDDLE_AMERICA_AGENTS.exists():
        md_files.extend(MIDDLE_AMERICA_AGENTS.glob("*.md"))
        print(f"Found {len(list(MIDDLE_AMERICA_AGENTS.glob('*.md')))} middle america prompts")

    # Industry standards examples
    if INDUSTRY_AGENTS.exists():
        md_files.extend(INDUSTRY_AGENTS.glob("*.md"))
        print(f"Found {len(list(INDUSTRY_AGENTS.glob('*.md')))} industry example prompts")

    print(f"\nTotal prompts to process: {len(md_files)}")
    print("-" * 60)

    # Process each file
    imported = 0
    skipped = 0
    errors = 0

    for md_path in md_files:
        template = convert_md_to_yaml(md_path)

        if template is None:
            skipped += 1
            continue

        # Write YAML file
        output_path = TEMPLATES_OUTPUT / f"{template['id']}.yaml"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(template, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            print(f"  Created: {template['id']}.yaml ({template['category']})")
            imported += 1
        except Exception as e:
            print(f"  Error writing {template['id']}: {e}")
            errors += 1

    print("-" * 60)
    print(f"\nImport Summary:")
    print(f"  Imported: {imported}")
    print(f"  Skipped:  {skipped}")
    print(f"  Errors:   {errors}")
    print(f"  Output:   {TEMPLATES_OUTPUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()

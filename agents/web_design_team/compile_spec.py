"""
Standalone spec compiler — reads all stage files and produces the
complete handoff specification. Runs independently of the design flow
so it can be re-run as many times as needed.
"""

import os
import asyncio
from pathlib import Path
from datetime import datetime
import structlog

from crewai import Agent, Task, Crew, Process, LLM

logger = structlog.get_logger()

STAGES_DIR = Path("/Volumes/Storage/LegacySiteTest/design_stages")
OUTPUT_DIR = Path("/Volumes/Storage/LegacySiteTest")

LEGACY_AI_CONTENT = """
COMPANY: LEGACY AI
FOUNDER/CEO: Douglas Talley
PHONE: 812.340.5761
EMAIL: Douglas.Talley@LegacyAI.space
ADDRESS: 6405 Justin's Ridge Road, Nashville, IN 47448
SERVICE AREA: Brown County, Columbus, Bloomington, Indianapolis, 100-mile radius
LINKEDIN: https://www.linkedin.com/in/douglasatalley/
INSTAGRAM: https://www.instagram.com/legacyaisolutions/
CALENDLY: https://calendly.com/legacyai
HOURS: Monday-Friday 9AM-6PM, Saturday 10AM-2PM

TAGLINE: "Bridging Generations of Experience with AI"
MISSION: "Embracing Experience, Empowering Innovation."

SERVICES:
1. Custom AI Solutions (/custom-solutions)
2. Remote Consultation (/remote-consultation)
3. In-House Services (/in-house-services)
4. AI Strategy & Roadmapping (/contact?service=strategy-workshop)
5. Knowledge System Support (/contact?service=support)
6. AI Ethics & Compliance Audit (/contact?service=ethics)
7. CRM-AI Pro (/crm-ai-pro)
8. AI Agents (/ai-agents)

TESTIMONIALS:
1. Michael Chen, CTO Global Manufacturing Inc — "What used to take months of shadowing now happens in weeks."
2. Sarah Johnson, General Counsel Enterprise Solutions — "40 years of expertise captured and still guiding our legal team."
3. David Rodriguez, Head of Innovation BioTech Innovations — "35% reduction in development time."
4. Robertson Family, Robertson Family Farms Indiana — "Generations of farming knowledge now accessible."
5. Jessica Miller, The Style Suite Salon — "Like having the perfect assistant."
6. Brian Evans CPA, Evans Accounting — "Find answers instantly."
7. Dr. Emily Wilson CMO, Regional Healthcare — "Critical procedures accessible to entire staff."
8. Robert Thompson, Heritage Manufacturing — "75 years of history preserved."

CURRENT TECH STACK:
- Next.js 16, TypeScript strict, Tailwind CSS
- Framer Motion
- Aceternity UI: AuroraBackground, LampEffect, EvervaultCard, MacbookScroll,
  AppleCardsCarousel, Globe, FloatingDock, 3DCard, BackgroundBeams,
  BackgroundGradient, AnimatedText, EncryptedText
- Dark theme, Inter + JetBrains Mono
- next-themes ThemeProvider

EXISTING PAGES:
/ (homepage), /about, /contact, /custom-solutions, /remote-consultation,
/in-house-services, /crm-ai-pro, /ai-agents
"""


async def compile():
    llm = LLM(
        model=os.getenv("DEFAULT_MODEL", "gpt-4o"),
        base_url="https://api.portkey.ai/v1",
        api_key=os.getenv("PORTKEY_API_KEY", ""),
    )

    # Load all stage files
    stages = {}
    for stage_file in sorted(STAGES_DIR.glob("*.md")):
        stages[stage_file.stem] = stage_file.read_text()
        print(f"Loaded: {stage_file.name} ({len(stages[stage_file.stem])} chars)")

    compiler = Agent(
        role="Expert Technical Specification Writer",
        goal="Write a complete, exhaustive, builder-ready website specification for Legacy AI",
        backstory="""You write specifications that builders execute without asking
a single question. Your specs contain the actual content — not summaries,
not references, not "see above." The actual hex codes. The actual copy, word
for word. The actual component names and props.

You are exhaustive by nature. When in doubt, you include more detail, not less.
A good spec is 30-50 pages. A bad spec is 6 pages with placeholders.""",
        llm=llm,
        verbose=True,
        max_iter=10,
    )

    task = Task(
        description=f"""
Write the COMPLETE, EXHAUSTIVE specification for the Legacy AI website rebuild.

You have access to all upstream research. Your job is to synthesize it into
one document that a developer can execute without asking a single question.

DO NOT SUMMARIZE. Include the actual content.
DO NOT USE PLACEHOLDERS like "(see above)" or "(include all sections)".
WRITE THE ACTUAL COPY, ACTUAL HEX CODES, ACTUAL COMPONENT PROPS.

---

## UPSTREAM RESEARCH

### COMPETITIVE ANALYSIS
{stages.get("01_competitive_analysis", "Not available")}

### UX ARCHITECTURE
{stages.get("02_ux_architecture", "Not available")}

### VISUAL DESIGN SYSTEM
{stages.get("03_visual_design", "Not available")}

### CONVERSION COPY
{stages.get("04_conversion_copy", "Not available")}

### TECHNICAL ARCHITECTURE
{stages.get("05_technical_architecture", "Not available")}

### REAL LEGACY AI CONTENT (PRESERVE ALL)
{LEGACY_AI_CONTENT}

---

## OUTPUT FORMAT

Produce a markdown document with these sections:

# Legacy AI — Complete Website Specification
*Date: {datetime.now().strftime("%Y-%m-%d")}*

## 1. Strategic Positioning
(Key differentiators, positioning statement, what makes Legacy AI unique)

## 2. Visual Design System

### Color Palette
(Every color with name, hex code, Tailwind class, and usage context)

### Typography
(Font names, scale with exact sizes/weights, Google Fonts import URL)

### CSS Variables
(Complete :root block for globals.css — copy-paste ready)

### Aceternity Component Theming
(For each component: exact prop values to use)

## 3. Site Architecture
(All pages with purpose, primary CTA, and key sections)

## 4. Page Specifications

### Homepage (/)
For each section in order:
- Section name
- Aceternity/custom component to use
- Exact props
- Full copy (word for word)
- Notes/gotchas

### About Page (/about)
(Same format)

### Contact Page (/contact)
(Same format — preserve all real contact info)

### Custom AI Solutions (/custom-solutions)
(Same format)

### Remote Consultation (/remote-consultation)
(Same format)

### In-House Services (/in-house-services)
(Same format)

### CRM-AI Pro (/crm-ai-pro)
(Same format)

### AI Agents (/ai-agents)
(Same format)

## 5. Complete Copy Reference
(All headlines, subheadlines, body copy, CTAs — organized by page and section)

## 6. Technical Implementation Guide
(globals.css update, implementation order, dynamic imports, known gotchas)

## 7. Real Content Reference
(Phone, email, address, social links, testimonials verbatim, FAQs)

---

Be thorough. Be specific. No placeholders. No summaries. The actual content.
""",
        expected_output="Complete exhaustive specification document, 30-50 pages of actual content",
        agent=compiler,
    )

    crew = Crew(
        agents=[compiler], tasks=[task], process=Process.sequential, verbose=True
    )
    result = await crew.kickoff_async()

    spec = str(result)

    # Save with timestamp
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{date_str}_Legacy_AI_Complete_Specification.md"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(spec)

    print(f"\n{'=' * 60}")
    print(f"SPEC COMPILED")
    print(f"{'=' * 60}")
    print(f"Size  : {len(spec):,} chars ({len(spec) // 1000}KB)")
    print(f"Path  : {output_path}")
    print(f"{'=' * 60}\n")

    return str(output_path)


if __name__ == "__main__":
    asyncio.run(compile())

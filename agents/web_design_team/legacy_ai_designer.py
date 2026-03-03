"""
================================================================================
            LEGACY AI WEB DESIGN TEAM
            "Building the World's Best AI Solutions Website"
================================================================================

                ██╗     ███████╗ ██████╗  █████╗  ██████╗██╗   ██╗
                ██║     ██╔════╝██╔════╝ ██╔══██╗██╔════╝╚██╗ ██╔╝
                ██║     █████╗  ██║  ███╗███████║██║      ╚████╔╝
                ██║     ██╔══╝  ██║   ██║██╔══██║██║       ╚██╔╝
                ███████╗███████╗╚██████╔╝██║  ██║╚██████╗   ██║
                ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝   ╚═╝

                        A 6-Agent Elite Design Team
                    Built specifically for Legacy AI

================================================================================
ARCHITECTURE: Godzilla Pattern
FLOW: Research → UX → Visual → Copy → Tech → Compile
VERSION: 1.0.0
OUTPUT: Complete spec + rebuilt Aceternity-compatible Next.js site
================================================================================
"""

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start
from crewai_tools import ScrapeWebsiteTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog
import os
import json

logger = structlog.get_logger()


# =============================================================================
# STATE
# =============================================================================


class LegacyAIDesignState(BaseModel):
    task_id: str = Field(default="")
    project_name: str = Field(default="Legacy AI Website")
    status: str = Field(default="pending")
    progress: float = Field(default=0.0)
    current_phase: str = Field(default="initialization")
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)

    competitive_analysis: Dict[str, Any] = Field(default_factory=dict)
    ux_architecture: Dict[str, Any] = Field(default_factory=dict)
    visual_design_system: Dict[str, Any] = Field(default_factory=dict)
    conversion_copy: Dict[str, Any] = Field(default_factory=dict)
    technical_architecture: Dict[str, Any] = Field(default_factory=dict)
    website_specification: Optional[str] = Field(default=None)
    specification_path: Optional[str] = Field(default=None)

    output_directory: str = Field(default="/Volumes/Storage/LegacySiteTest")
    created_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


# =============================================================================
# REAL LEGACY AI CONTENT (preserved exactly — this feeds every agent)
# =============================================================================

LEGACY_AI_CONTENT = """
# LEGACY AI — Real Business Content (Preserve All of This)

## Identity
- Company: LEGACY AI
- Founder/CEO: Douglas Talley
- Tagline: "Bridging Generations of Experience with AI"
- Phone: 812.340.5761
- Email: Douglas.Talley@LegacyAI.space
- Address: 6405 Justin's Ridge Road, Nashville, IN 47448
- Service area: Brown County, Columbus, Bloomington, Indianapolis, 100-mile radius
- LinkedIn: https://www.linkedin.com/in/douglasatalley/
- Instagram: https://www.instagram.com/legacyaisolutions/
- Calendly: https://calendly.com/legacyai

## Core Mission
"At Legacy, we believe that experience is invaluable and should be celebrated.
Our mission is to bridge timeless human wisdom with cutting-edge AI technology,
enabling individuals of all backgrounds to harness artificial intelligence in ways
that authentically enhance their lives."

"Legacy stands at the intersection of human experience and technological
advancement—ensuring that wisdom is never lost but rather enhanced, extended,
and preserved."

"Embracing Experience, Empowering Innovation."

## Services
1. Custom AI Solutions — Tailored AI systems to capture, preserve, and enhance
   organizational knowledge assets. (/custom-solutions)
2. Remote Consultation — Expert guidance for AI implementation, anywhere. (/remote-consultation)
3. In-House Services — On-site expertise for knowledge management. (/in-house-services)
4. AI Strategy & Roadmapping — Strategic planning workshops for AI adoption.
5. Knowledge System Support — Ongoing maintenance, updates, user support.
6. AI Ethics & Compliance Audit — Expert audits for fairness, privacy, regulatory compliance.
7. CRM-AI Pro — AI-enhanced CRM system. (/crm-ai-pro)
8. AI Agents — Autonomous agent solutions. (/ai-agents)

## Value Propositions
- Knowledge Preservation: Capture critical expertise before it walks out the door
- Accelerated Innovation: Build on collective wisdom for faster innovation
- Enhanced Efficiency: Make institutional knowledge accessible and actionable
- Improved Collaboration: Break down silos through shared knowledge
- Faster Onboarding: Get new team members up to speed quickly
- Risk Mitigation: Reduce impact of key personnel departures

## Real Testimonials
1. Michael Chen - CTO, Global Manufacturing Inc. (Manufacturing)
   "LEGACY AI's solution has transformed how we onboard new team members. What
   used to take months of shadowing now happens in weeks."

2. Sarah Johnson - General Counsel, Enterprise Solutions (Legal)
   "When our senior legal counsel with 40 years of experience retired, we thought
   we'd lose decades of invaluable knowledge. LEGACY AI helped us capture that
   expertise in an AI system that continues to guide our legal team today."

3. David Rodriguez - Head of Innovation, BioTech Innovations (Biotech)
   "We've reduced development time by 35% while improving success rates."

4. The Robertson Family - Robertson Family Farms, Central Indiana (Agriculture)
   "Generations of farming knowledge felt impossible to pass on effectively.
   LEGACY AI helped us build a system using sensor data and family logs."

5. Jessica Miller - Owner, The Style Suite Salon (Retail)
   "My custom AI agent is like having the perfect assistant! It reminds me of
   client style preferences, product allergies, even little details about their
   families or pets before appointments."

6. Brian Evans - CPA, Evans Accounting Services (Professional Services)
   "LEGACY AI built a knowledge base combined with an AI assistant that helps me
   find answers instantly."

7. Dr. Emily Wilson - CMO, Regional Healthcare (Healthcare)
   "Critical procedures and best practices from our most experienced physicians
   are now accessible to our entire medical staff."

8. Robert Thompson - Operations Director, Heritage Manufacturing
   "75 years of history, we were losing critical knowledge with each retirement.
   LEGACY AI helped us digitize and enhance our institutional knowledge."

## Target Markets
- Indiana SMBs (primary)
- Healthcare organizations
- Manufacturing companies
- Legal practices
- Agricultural businesses
- Professional services (accounting, architecture, etc.)
- Educational institutions
- Retail businesses

## Current Tech Stack (Aceternity-style)
- Next.js 16, TypeScript, Tailwind CSS
- Framer Motion animations
- Aceternity UI components: Aurora Background, Lamp Effect, Evervault Card,
  MacBook Scroll, Apple Cards Carousel, Globe, Floating Dock, 3D Card
- Dark theme with purple/blue accents
- Inter + JetBrains Mono fonts

## Business Hours
Monday - Friday: 9:00 AM - 6:00 PM
Saturday: 10:00 AM - 2:00 PM

## FAQs (Real)
- Industries: healthcare, manufacturing, financial, legal, agriculture, retail, education
- Implementation: 4-12 weeks for custom solutions
- Security: GDPR, HIPAA, CCPA compliant, end-to-end encryption
- Support: 90-day minimum support period included
"""


# =============================================================================
# FLOW
# =============================================================================


class LegacyAIDesignFlow(Flow[LegacyAIDesignState]):
    """
    6-agent design team built specifically for Legacy AI.
    Researches the AI solutions market, then produces a complete
    spec and rebuilt Aceternity-compatible website.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = self._get_llm()
        self.scraper = ScrapeWebsiteTool()
        self.stages_dir = Path("/Volumes/Storage/LegacySiteTest/design_stages")
        self.stages_dir.mkdir(parents=True, exist_ok=True)

    def _save_stage(self, name: str, content: str) -> Path:
        """Save a stage's full output to disk."""
        path = self.stages_dir / f"{name}.md"
        path.write_text(content)
        logger.info("Stage saved", name=name, size=len(content), path=str(path))
        return path

    def _load_stage(self, name: str, max_chars: int = 50000) -> str:
        """Load a stage's full output from disk."""
        path = self.stages_dir / f"{name}.md"
        if path.exists():
            content = path.read_text()
            logger.info("Stage loaded", name=name, size=len(content))
            return content[:max_chars]
        return ""

    def _get_llm(self) -> LLM:
        provider = os.getenv("LAIAS_LLM_PROVIDER", "openai")
        if provider == "zai":
            return LLM(
                model="glm-4-plus",
                api_key=os.getenv("ZAI_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4",
            )
        return LLM(model="gpt-4o")

    # =========================================================================
    # STAGE 1: COMPETITIVE RESEARCH
    # =========================================================================

    @start()
    async def research_competition(self) -> LegacyAIDesignState:
        """Research the AI solutions market and Legacy AI's competitors."""
        if not self.state.task_id:
            self.state.task_id = f"legacyai_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.state.created_at = datetime.utcnow().isoformat()
        self.state.status = "researching"
        self.state.progress = 5.0
        self.state.current_phase = "competitive_research"

        logger.info("Stage 1: Competitive Research", task_id=self.state.task_id)

        analyst = Agent(
            role="Senior Competitive Intelligence Analyst",
            goal="Research the AI solutions market and identify how Legacy AI can dominate it",
            backstory="""You are a world-class competitive intelligence analyst specializing
in the AI consulting and solutions space. You have deep knowledge of how AI service
companies position themselves online, what design patterns work for converting
prospects into clients, and what gaps exist in the market.

You research real competitors, identify their strengths and weaknesses, and
produce actionable intelligence that will shape a website redesign.

You know that Legacy AI is different: they're Indiana-based, they focus on
KNOWLEDGE PRESERVATION (not just automation), they serve SMBs and communities,
and their founder Douglas Talley is the human face of the brand.""",
            llm=self.llm,
            tools=[self.scraper],
            verbose=True,
            max_iter=25,
        )

        task = Task(
            description=f"""
Research the competitive landscape for Legacy AI and produce a comprehensive
competitive intelligence report that will guide a complete website redesign.

LEGACY AI CONTEXT:
{LEGACY_AI_CONTENT}

YOUR RESEARCH MUST COVER:

## 1. MARKET POSITIONING ANALYSIS
Analyze how top AI consulting/solutions companies position themselves online:
- What messaging do they lead with?
- What visual design patterns dominate? (dark vs light, animated vs static)
- What CTAs convert best in this space?
- How do they handle trust signals?
- What's missing that Legacy AI can own?

Consider companies like:
- IBM Consulting AI (enterprise)
- Accenture AI (enterprise)
- smaller boutique AI consultancies
- Indiana-based tech companies
- Knowledge management platforms

## 2. LEGACY AI DIFFERENTIATION
What makes Legacy AI genuinely different:
- "Knowledge preservation" vs. generic "AI automation" — this is rare positioning
- Indiana roots, personal touch, SMB focus
- Human-centered approach (experience + technology)
- Douglas Talley as founder/face of brand
- Real testimonials across diverse industries

## 3. DESIGN PATTERN ANALYSIS
What design patterns work for AI consulting sites:
- Aceternity/Framer-style animations: are they used by competitors? What's the effect?
- Dark theme vs light theme: which converts better in this space?
- Social proof placement and format
- Service presentation patterns
- Contact/conversion flow best practices

## 4. GAPS AND OPPORTUNITIES
What can Legacy AI do that nobody else in this space is doing:
- Specific content gaps
- Feature gaps (interactive demos, calculators, etc.)
- Positioning gaps
- Geographic differentiators (Indiana is an underserved market)

## 5. RECOMMENDED POSITIONING STATEMENT
One sharp sentence that only Legacy AI can own.

## 6. FEATURE PRIORITY LIST
Rank the top 10 features/improvements for the redesign by conversion impact.

Produce a thorough, specific, actionable report. This feeds the entire redesign.
""",
            expected_output="Comprehensive competitive intelligence report with specific recommendations",
            agent=analyst,
        )

        crew = Crew(
            agents=[analyst], tasks=[task], process=Process.sequential, verbose=True
        )
        result = await crew.kickoff_async()

        output = str(result)
        self._save_stage("01_competitive_analysis", output)
        self.state.competitive_analysis = {
            "raw_output": output,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.progress = 20.0
        logger.info("Stage 1 complete: Competitive Research", chars=len(output))
        return self.state

    # =========================================================================
    # STAGE 2: UX ARCHITECTURE
    # =========================================================================

    @listen("research_competition")
    async def design_ux(self) -> LegacyAIDesignState:
        """Design the complete UX architecture."""
        if self.state.error_count > 2:
            return self.state

        self.state.status = "designing_ux"
        self.state.progress = 25.0
        self.state.current_phase = "ux_architecture"
        logger.info("Stage 2: UX Architecture")

        ux = Agent(
            role="Principal UX Architect",
            goal="Design a world-class user experience for Legacy AI that converts visitors into clients",
            backstory="""You are a legendary UX architect who has designed experiences
for companies like Stripe, Linear, and Vercel. You understand that for a boutique
AI consulting firm, the website IS the first impression — it needs to feel
premium, trustworthy, and human at the same time.

You know the Aceternity UI library deeply. You design experiences that use
Aurora backgrounds, Lamp effects, Evervault cards, and MacBook Scroll components
in ways that feel intentional, not showy.

Your north star: every person who lands on this site should feel "these people
get me" within 3 seconds.""",
            llm=self.llm,
            verbose=True,
            max_iter=25,
        )

        task = Task(
            description=f"""
Design the complete UX architecture for the Legacy AI website redesign.

LEGACY AI CONTENT:
{LEGACY_AI_CONTENT}

COMPETITIVE RESEARCH:
{self.state.competitive_analysis.get("raw_output", "")[:3000]}

DESIGN THE FOLLOWING:

## 1. SITE ARCHITECTURE
Complete sitemap with all pages:
- Homepage (primary conversion page)
- About (/about)
- Services overview
- Custom AI Solutions (/custom-solutions)
- Remote Consultation (/remote-consultation)
- In-House Services (/in-house-services)
- CRM-AI Pro (/crm-ai-pro)
- AI Agents (/ai-agents)
- Contact (/contact)

For each page: purpose, primary CTA, key sections, success metric.

## 2. HOMEPAGE FLOW (Most Critical)
Design the exact scroll journey:
1. Hero section — what's the hook?
2. Trust signal — what goes here?
3. Social proof — how is it presented?
4. Services — how are they shown?
5. Philosophy/About — how much detail?
6. Final CTA — what drives the call?

Consider the existing Aceternity components already in use:
- AuroraBackground (hero)
- Globe (service area)
- LampEffect (philosophy sections)
- EvervaultCard (contact info, features)
- MacbookScroll (product demo)
- AppleCardsCarousel (testimonials)

Which of these should stay? Which should be repositioned? What's missing?

## 3. CONVERSION FUNNEL
- Primary conversion: schedule Calendly call
- Secondary conversion: contact form submit
- Tertiary conversion: phone call

Where does each happen and how is it triggered?

## 4. MOBILE-FIRST CONSIDERATIONS
The Aceternity components are heavy. How do we ensure mobile performance
without gutting the visual experience?

## 5. NAVIGATION DESIGN
Current: Floating dock (macOS style). Is this the right choice?
Redesign or refine the navigation pattern.

## 6. PAGE-BY-PAGE WIREFRAMES
For each major page, provide a text wireframe:
- Section names and order
- Component recommendations (which Aceternity component fits each section)
- Content blocks needed
- CTA placement

Be specific and opinionated. This feeds the builder directly.
""",
            expected_output="Complete UX architecture with page-by-page wireframes and component recommendations",
            agent=ux,
        )

        crew = Crew(agents=[ux], tasks=[task], process=Process.sequential, verbose=True)
        result = await crew.kickoff_async()

        output = str(result)
        self._save_stage("02_ux_architecture", output)
        self.state.ux_architecture = {
            "raw_output": output,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.progress = 40.0
        logger.info("Stage 2 complete: UX Architecture", chars=len(output))
        return self.state

    # =========================================================================
    # STAGE 3: VISUAL DESIGN SYSTEM
    # =========================================================================

    @listen("design_ux")
    async def design_visual_system(self) -> LegacyAIDesignState:
        """Create the visual design system."""
        if self.state.error_count > 2:
            return self.state

        self.state.status = "designing_visual"
        self.state.progress = 45.0
        self.state.current_phase = "visual_design"
        logger.info("Stage 3: Visual Design System")

        designer = Agent(
            role="Creative Director & Design System Architect",
            goal="Create a stunning visual design system for Legacy AI that feels premium yet human",
            backstory="""You are a world-class creative director who specializes in
dark-mode SaaS and AI company branding. You've worked on Vercel, Linear, and
Raycast's visual identities. You understand how to make a dark theme feel warm
rather than cold.

You know the Tailwind CSS system inside out. Every color you specify is a
Tailwind class or CSS variable. You don't design in the abstract — you design
in code-ready specifications.

For Legacy AI specifically: the brand needs to feel like the intersection of
"veteran wisdom" and "cutting-edge tech." Think deep navy and warm amber, not
cold blue-white. Think trust, depth, and competence.""",
            llm=self.llm,
            verbose=True,
            max_iter=25,
        )

        task = Task(
            description=f"""
Create a complete visual design system for the Legacy AI website redesign.

CURRENT STACK: Next.js 16, Tailwind CSS, Framer Motion, Aceternity UI, dark theme
CURRENT ACCENT: purple/blue

CONTEXT:
{LEGACY_AI_CONTENT[:1500]}

UX ARCHITECTURE:
{self.state.ux_architecture.get("raw_output", "")[:2000]}

DESIGN THE FOLLOWING:

## 1. BRAND COLOR PALETTE
Provide exact values as Tailwind classes AND hex codes:

Primary brand color (trust + premium) — consider moving away from generic blue
Secondary color (warmth, humanity)
Accent/CTA color (action)
Background colors (multiple depths for layering)
Text colors (primary, secondary, muted)
Border colors
Glow colors for Aceternity components

The current purple/blue — should it stay, evolve, or be replaced entirely?
Make a bold recommendation with reasoning.

## 2. TYPOGRAPHY SYSTEM
- Primary font: Google Font recommendation (currently Inter)
- Mono font: (currently JetBrains Mono)
- Heading scale: h1 through h6 with exact sizes and weights
- Body copy sizes and line heights
- Special text treatments (gradient text, glowing text, encrypted text)

## 3. ACETERNITY COMPONENT THEMING
For each Aceternity component in the project, specify exact theme values:
- AuroraBackground: colors array, intensity
- LampEffect: primary color
- EvervaultCard: glowColor per usage context
- Globe: arc colors, dot color
- MacbookScroll: gradient colors
- AppleCardsCarousel: card background

## 4. SPACING & LAYOUT
- Section padding standards (mobile / desktop)
- Container max-widths per section type
- Card border radius standards
- Consistent gap values

## 5. ANIMATION STANDARDS
Framer Motion timing standards:
- Page enter animations
- Section reveal animations
- Hover state transitions
- Component-specific animations

## 6. DARK THEME CSS VARIABLES
Provide the complete updated globals.css :root block with all CSS custom properties.

Make this beautiful and specific. The builder will implement exactly what you specify.
""",
            expected_output="Complete visual design system with hex codes, Tailwind classes, CSS variables, and component theming",
            agent=designer,
        )

        crew = Crew(
            agents=[designer], tasks=[task], process=Process.sequential, verbose=True
        )
        result = await crew.kickoff_async()

        output = str(result)
        self._save_stage("03_visual_design", output)
        self.state.visual_design_system = {
            "raw_output": output,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.progress = 58.0
        logger.info("Stage 3 complete: Visual Design System", chars=len(output))
        return self.state

    # =========================================================================
    # STAGE 4: CONVERSION COPY
    # =========================================================================

    @listen("design_visual_system")
    async def write_copy(self) -> LegacyAIDesignState:
        """Write conversion-optimized copy."""
        if self.state.error_count > 2:
            return self.state

        self.state.status = "writing_copy"
        self.state.progress = 62.0
        self.state.current_phase = "copywriting"
        logger.info("Stage 4: Conversion Copy")

        copywriter = Agent(
            role="Elite Conversion Copywriter",
            goal="Write copy for Legacy AI that converts Indiana business owners into clients",
            backstory="""You are one of the world's best conversion copywriters.
You've written for boutique consulting firms, AI startups, and B2B service
companies. You know that the best copy for a firm like Legacy AI isn't corporate
jargon — it's human, specific, and direct.

You deeply understand Douglas Talley's voice from reading his existing copy:
- He's earnest and genuine
- He believes in experience and wisdom
- He's based in rural Indiana (Nashville, not Nashville TN)
- He serves real small businesses, farms, salons, accounting firms
- He's not trying to compete with IBM — he's the guy who shows up and actually helps

You preserve the soul of the existing copy while making it sharper and more
conversion-focused. You don't replace real testimonials — you frame them better.
You don't invent new services — you make the existing ones irresistible.""",
            llm=self.llm,
            verbose=True,
            max_iter=25,
        )

        task = Task(
            description=f"""
Write all conversion copy for the Legacy AI website redesign.

REAL CONTENT TO WORK WITH:
{LEGACY_AI_CONTENT}

COMPETITIVE CONTEXT:
{self.state.competitive_analysis.get("raw_output", "")[:1500]}

UX ARCHITECTURE:
{self.state.ux_architecture.get("raw_output", "")[:1500]}

WRITE COPY FOR:

## HOMEPAGE

### Hero Section (5 headline options + 1 winner)
- Primary headline options — what's the hook?
- Subheadline — expand the promise
- CTA button text (primary + secondary)
- Trust badge/pill text

The current headline: "Bridging Generations of Experience with AI"
Is this the best we can do? Write 5 alternatives and pick the winner.

### Globe/Service Area Section
Improve the "Indiana Roots. Regional Reach." section copy.
Make it feel proud and specific, not just geographic.

### Philosophy Section
Improve the three missionParagraphs. Same ideas, sharper sentences.
Keep "Embracing Experience, Empowering Innovation." — it's good.

### Services Section
Improve each of the 6 service descriptions.
One sentence hook + one sentence proof per service.

### Why Choose Section
Improve each of the 6 benefit descriptions.
Make them specific, not generic.

### Testimonials Section Headline
Improve "What Our Clients Say" — make it more evocative.

### Final CTA Section
Improve "Ready to preserve and enhance your organization's legacy?"
Give 3 alternatives.

## ABOUT PAGE
- Improved hero headline + subheadline
- Story section: same facts, sharper narrative
- Mission section: tighter, more specific
- Values: better micro-copy for each value

## CONTACT PAGE
- Hero section improvements
- Form labels and microcopy
- FAQ answers: same info, cleaner prose

## META COPY (SEO)
- Homepage title tag (under 60 chars)
- Homepage meta description (under 160 chars)
- About, Contact, Services meta descriptions

Write like a human, not a marketing robot.
Every word must earn its place.
""",
            expected_output="Complete copy document covering all pages with clear section labels",
            agent=copywriter,
        )

        crew = Crew(
            agents=[copywriter], tasks=[task], process=Process.sequential, verbose=True
        )
        result = await crew.kickoff_async()

        output = str(result)
        self._save_stage("04_conversion_copy", output)
        self.state.conversion_copy = {
            "raw_output": output,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.progress = 75.0
        logger.info("Stage 4 complete: Conversion Copy", chars=len(output))
        return self.state

    # =========================================================================
    # STAGE 5: TECHNICAL ARCHITECTURE
    # =========================================================================

    @listen("write_copy")
    async def design_tech_architecture(self) -> LegacyAIDesignState:
        """Design the technical implementation architecture."""
        if self.state.error_count > 2:
            return self.state

        self.state.status = "designing_tech"
        self.state.progress = 78.0
        self.state.current_phase = "technical_architecture"
        logger.info("Stage 5: Technical Architecture")

        architect = Agent(
            role="Principal Next.js Architect",
            goal="Design the technical implementation plan for the Legacy AI redesign",
            backstory="""You are a senior Next.js architect who specializes in
Aceternity UI, Framer Motion, and high-performance dark-theme websites. You've
built sites exactly like this one — heavy animations, complex components, dark
backgrounds.

You know every gotcha:
- Aceternity components often need 'use client' and specific import patterns
- Globe.tsx is heavy — needs dynamic import with SSR disabled
- MacbookScroll needs overflow:visible on parent containers
- AuroraBackground needs pointer-events:none when used as a background layer
- Framer Motion AnimatePresence needs to wrap conditional renders

You produce specs that eliminate ambiguity. The builder reads your output and
has zero questions.""",
            llm=self.llm,
            verbose=True,
            max_iter=20,
        )

        task = Task(
            description=f"""
Design the complete technical implementation plan for the Legacy AI website redesign.

CURRENT STACK:
- Next.js 16 (App Router)
- TypeScript (strict)
- Tailwind CSS with custom CSS variables
- Framer Motion
- Aceternity UI components (custom implementations in components/ui/)
- Biome formatter, oxlint, secretlint
- Dark theme via next-themes ThemeProvider

CURRENT COMPONENTS AVAILABLE:
3d-card.tsx, 3d-pin.tsx, animated-text.tsx, apple-cards-carousel.tsx,
aurora-background.tsx, background-beams.tsx, background-gradient.tsx,
button.tsx, card.tsx, container-scroll-animation.tsx, container.tsx,
dotted-glow-bg.tsx, encrypted-text.tsx, enhanced-hero.tsx, evervault-card.tsx,
feature-sections.tsx, floating-dock.tsx, footer.tsx, globe.tsx, input.tsx,
lamp-effect.tsx, macbook-scroll.tsx, navbar.tsx, section.tsx, stateful-button.tsx,
testimonial-carousel.tsx

DESIGN THE FOLLOWING:

## 1. FILE STRUCTURE
What files need to be created/modified:
- New page files (app/*/page.tsx)
- Component modifications needed
- New components to add
- globals.css changes

## 2. COMPONENT USAGE GUIDE
For each page, specify EXACTLY which components to use in which sections:
- Component name, import path, key props
- Known gotchas and how to avoid them
- SSR/client directives needed

## 3. PERFORMANCE STRATEGY
The Aceternity components are expensive. How do we ensure:
- LCP < 2.5s
- No layout shift from heavy components
- Mobile performance acceptable
- Lazy loading strategy for Globe, MacbookScroll

## 4. GLOBALS.CSS UPDATE
Specify the complete new :root CSS variables block based on the new design system.

## 5. IMPLEMENTATION ORDER
The sequence a builder should follow to minimize re-work:
1. globals.css first
2. Then which files in what order

## 6. KNOWN ACETERNITY GOTCHAS
List every known issue with the current components and how to handle them:
- The 'use client' requirements
- The overflow issues
- The SSR issues
- The TypeScript issues

Make this so specific that the builder has zero questions.
""",
            expected_output="Complete technical implementation plan with component usage guide and implementation order",
            agent=architect,
        )

        crew = Crew(
            agents=[architect], tasks=[task], process=Process.sequential, verbose=True
        )
        result = await crew.kickoff_async()

        output = str(result)
        self._save_stage("05_technical_architecture", output)
        self.state.technical_architecture = {
            "raw_output": output,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.progress = 88.0
        logger.info("Stage 5 complete: Technical Architecture", chars=len(output))
        return self.state

    # =========================================================================
    # STAGE 6: COMPILE SPEC
    # =========================================================================

    @listen("design_tech_architecture")
    async def compile_specification(self) -> LegacyAIDesignState:
        """Compile everything into the handoff-ready specification."""
        if self.state.error_count > 2:
            return self.state

        self.state.status = "compiling"
        self.state.progress = 90.0
        self.state.current_phase = "compilation"
        logger.info("Stage 6: Compiling Final Specification")

        compiler = Agent(
            role="Technical Documentation Lead",
            goal="Compile all work into a single, handoff-ready specification for the builder agent",
            backstory="""You compile specifications that builders can execute without
asking a single question. Your specs are legendary for their clarity, completeness,
and specificity. You never say "approximately" or "something like." You say exactly.

For Legacy AI, the builder needs to know:
- Every color by hex value AND Tailwind class
- Every section in every page, in order
- Every component with its exact props
- Every piece of copy, word for word
- Every technical decision and why it was made

You synthesize all the upstream work into one document that is the single source
of truth for the entire rebuild.""",
            llm=self.llm,
            verbose=True,
            max_iter=20,
        )

        # Load full stage outputs from disk — no truncation
        competitive = self._load_stage("01_competitive_analysis")
        ux = self._load_stage("02_ux_architecture")
        visual = self._load_stage("03_visual_design")
        copy = self._load_stage("04_conversion_copy")
        tech = self._load_stage("05_technical_architecture")

        task = Task(
            description=f"""
Compile ALL upstream work into a single, complete, handoff-ready specification.

COMPETITIVE ANALYSIS:
{competitive}

UX ARCHITECTURE:
{ux}

VISUAL DESIGN SYSTEM:
{visual}

CONVERSION COPY:
{copy}

TECHNICAL ARCHITECTURE:
{tech}

REAL LEGACY AI CONTENT:
{LEGACY_AI_CONTENT}

COMPILE INTO:

# Legacy AI Website — Complete Redesign Specification

## Part 1: Strategic Positioning
(From competitive analysis — positioning, differentiation, opportunities)

## Part 2: Visual Design System
(Complete CSS variables, color palette with hex + Tailwind, typography, spacing)

## Part 3: Component Library
(Which Aceternity components to use where, with exact props and gotchas)

## Part 4: Page-by-Page Specification

### Homepage
- Section 1: [name] — component, copy, props
- Section 2: [name] — ...
(Continue for all sections)

### About Page
(Same format)

### Contact Page
(Same format)

### Services Pages
(Same format for each)

## Part 5: Complete Copy Document
(All final copy, word for word, for every section)

## Part 6: Technical Implementation Guide
(globals.css update, implementation order, known gotchas, dynamic imports needed)

## Part 7: Real Content Reference
(Preserved: phone, email, address, social links, testimonials, FAQs)

FORMAT: Use Markdown. Be exhaustive. The builder reads this and asks zero questions.
This document is the law. Everything the builder builds must match this spec exactly.
""",
            expected_output="Complete specification document in Markdown, structured for builder consumption",
            agent=compiler,
        )

        crew = Crew(
            agents=[compiler], tasks=[task], process=Process.sequential, verbose=True
        )
        result = await crew.kickoff_async()

        spec_content = str(result)

        # Save to output directory
        output_dir = Path(self.state.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_Legacy_AI_Website_Specification.md"
        spec_path = output_dir / filename

        spec_path.write_text(spec_content)

        self.state.website_specification = spec_content
        self.state.specification_path = str(spec_path)
        self.state.progress = 100.0
        self.state.status = "completed"
        self.state.completed_at = datetime.utcnow().isoformat()

        logger.info(
            "Specification compiled and saved",
            path=str(spec_path),
            size=len(spec_content),
        )

        return self.state


# =============================================================================
# MAIN
# =============================================================================


async def main():
    import asyncio

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              LEGACY AI — WEB DESIGN TEAM                                    ║
║              "Building the World's Best AI Solutions Website"               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Stage 1: Competitive Research  → Market analysis, positioning gaps        ║
║  Stage 2: UX Architecture       → Page flows, wireframes, components       ║
║  Stage 3: Visual Design System  → Colors, typography, Aceternity theming   ║
║  Stage 4: Conversion Copy       → All page copy, CTAs, micro-copy          ║
║  Stage 5: Technical Architecture → Implementation plan, gotchas, order     ║
║  Stage 6: Specification Compiler → Complete handoff doc for builder        ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    flow = LegacyAIDesignFlow()

    await flow.kickoff_async(
        inputs={
            "output_directory": "/Volumes/Storage/LegacySiteTest",
        }
    )

    print("\n" + "=" * 78)
    print("DESIGN TEAM COMPLETE")
    print("=" * 78)
    print(f"Status   : {flow.state.status}")
    print(f"Progress : {flow.state.progress}%")
    print(f"Spec     : {flow.state.specification_path}")
    print(f"Size     : {len(flow.state.website_specification or '')} chars")
    print("=" * 78)

    return flow.state.specification_path


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

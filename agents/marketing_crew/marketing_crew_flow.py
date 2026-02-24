"""
================================================================================
          LEGACY AI MARKETING TEAM — "One Building, Usually Closed"
================================================================================

A 5-agent marketing crew for Legacy AI, a one-person shop in Brown County,
Indiana. Generates content, social posts, SEO-optimized blog drafts, and
newsletters — all in the Legacy AI voice (BALLS-compliant, zero corporate speak).

Agents:
  1. Content Strategist — plans what to write and why
  2. Content Writer    — drafts long-form in the Legacy AI voice
  3. Social Media Mgr  — reformats for LinkedIn / X / GitHub
  4. SEO Specialist     — optimizes for discoverability
  5. Brand Coordinator  — final gatekeeper ("Would a guy in the woods say this?")

Flow:
  initialize → strategize → write_content → [social_media, seo_optimize]
      → brand_review → (approve | revise) → finalize

Follows the Godzilla architectural pattern exactly.
Author: LAIAS Agent Generator
Date: February 2026
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai.flow.persistence import persist
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog
import yaml
import os

# =============================================================================
# LOGGING
# =============================================================================

logger = structlog.get_logger()

# =============================================================================
# LOAD BRAND ASSETS
# =============================================================================

_HERE = Path(__file__).parent
STYLE_GUIDE_PATH = _HERE / "style_guide" / "VOICE_AND_STYLE.md"
AGENTS_CONFIG_PATH = _HERE / "agents.yaml"


def _load_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def _load_yaml(path: Path) -> Dict[str, Any]:
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


STYLE_GUIDE = _load_text(STYLE_GUIDE_PATH)
AGENTS_CFG = _load_yaml(AGENTS_CONFIG_PATH)

# =============================================================================
# SECTION 1: TYPED STATE
# =============================================================================


class MarketingState(BaseModel):
    """Typed state for the marketing crew flow."""

    # === Execution Identity ===
    task_id: str = Field(default="", description="Unique task identifier")
    status: str = Field(default="pending", description="Current execution status")

    # === Error Handling ===
    error_count: int = Field(default=0, description="Errors encountered")
    last_error: Optional[str] = Field(default=None, description="Most recent error")

    # === Progress ===
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion %")
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Brand-voice score"
    )

    # === Inputs ===
    topic: str = Field(default="", description="What the content is about")
    content_type: str = Field(
        default="blog",
        description="blog | newsletter | announcement | social-only",
    )
    target_platforms: List[str] = Field(
        default_factory=lambda: ["linkedin", "twitter"],
        description="Social platforms to target",
    )
    raw_notes: str = Field(
        default="", description="Raw notes / bullet points from user"
    )
    reference_docs: str = Field(
        default="", description="Reference material (brand docs, etc.)"
    )

    # === Pipeline Outputs ===
    content_strategy: str = Field(
        default="", description="Content plan from strategist"
    )
    long_form_draft: str = Field(default="", description="Blog / newsletter body")
    social_posts: Dict[str, str] = Field(
        default_factory=dict, description="Platform → post text"
    )
    seo_suggestions: str = Field(
        default="", description="SEO keywords, meta, title options"
    )
    brand_review_notes: str = Field(
        default="", description="Brand coordinator feedback"
    )
    final_content: Dict[str, str] = Field(
        default_factory=dict, description="Approved deliverables keyed by type"
    )

    # === Metadata ===
    revision_count: int = Field(default=0, description="Times sent back for revision")
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)


# =============================================================================
# SECTION 2: CONFIGURATION
# =============================================================================


class MarketingConfig(BaseModel):
    """Configuration for the marketing crew."""

    default_model: str = "openai/gpt-4o"
    writer_temperature: float = 0.85  # Creative for writing
    strategist_temperature: float = 0.6
    reviewer_temperature: float = 0.3  # Strict for brand review
    max_revisions: int = 2
    verbose: bool = True
    memory_enabled: bool = True


# =============================================================================
# SECTION 3: ANALYTICS
# =============================================================================


class MarketingAnalytics:
    """Simple execution tracking."""

    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "api_calls": 0,
            "total_cost": 0.0,
            "start_time": None,
            "end_time": None,
        }

    def start(self, task_id: str):
        self.metrics["start_time"] = datetime.utcnow().isoformat()
        logger.info("Marketing analytics started", task_id=task_id)

    def record(self, cost: float = 0.0):
        self.metrics["api_calls"] += 1
        self.metrics["total_cost"] += cost

    def end(self) -> Dict[str, Any]:
        self.metrics["end_time"] = datetime.utcnow().isoformat()
        logger.info(
            "Marketing analytics ended",
            api_calls=self.metrics["api_calls"],
            total_cost=self.metrics["total_cost"],
        )
        return self.metrics


# =============================================================================
# SECTION 4: THE FLOW
# =============================================================================


@persist
class LegacyMarketingFlow(Flow[MarketingState]):
    """
    Legacy AI Marketing Team — Godzilla pattern.

    FLOW DIAGRAM:

        ┌──────────────┐
        │  initialize   │ (@start)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  strategize   │ (@listen)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │write_content  │ (@listen)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │create_social  │ (@listen)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │ seo_optimize  │ (@listen)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │ brand_review  │ (@listen)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  @router      │ (conditional)
        └───┬──────┬───┘
            │      │
         approve  revise
            │      │
            ▼      ▼
        finalize  write_content (loop back)
    """

    def __init__(self, config: Optional[MarketingConfig] = None):
        super().__init__()
        self.config = config or MarketingConfig()
        self.analytics = MarketingAnalytics()
        self.style_guide = STYLE_GUIDE
        self.agents_cfg = AGENTS_CFG

        logger.info(
            "LegacyMarketingFlow initialized",
            model=self.config.default_model,
        )

    # =========================================================================
    # AGENT FACTORIES
    # =========================================================================

    def _create_content_strategist(self) -> Agent:
        return Agent(
            role="Content Strategist",
            goal="Plan content that drives visibility for a one-person AI shop",
            backstory=(
                "You plan marketing content for Legacy AI — a solo developer "
                "in Brown County, Indiana who builds open-source AI tools. "
                "You understand the audience: developers tired of subscription "
                "AI, indie hackers, and people who want to own their tools. "
                "You think in terms of hooks, angles, and distribution — not "
                "corporate marketing funnels."
            ),
            llm=LLM(
                model=self.config.default_model,
                temperature=self.config.strategist_temperature,
            ),
            verbose=self.config.verbose,
            memory=self.config.memory_enabled,
        )

    def _create_content_writer(self) -> Agent:
        cfg = self.agents_cfg.get("CONTENT_WRITER", {})
        return Agent(
            role=cfg.get("role", "Content Writer"),
            goal=cfg.get(
                "goal",
                "Write authentic content that sounds like a real human, not a marketing department",
            ),
            backstory=cfg.get(
                "backstory",
                "You write for Legacy AI. Conversational, self-deprecating, honest. "
                "No corporate speak. Final rule: Would a guy in the woods say this?",
            ),
            llm=LLM(
                model=self.config.default_model,
                temperature=self.config.writer_temperature,
            ),
            verbose=self.config.verbose,
            memory=self.config.memory_enabled,
        )

    def _create_social_media_manager(self) -> Agent:
        cfg = self.agents_cfg.get("SOCIAL_MEDIA_MANAGER", {})
        return Agent(
            role=cfg.get("role", "Social Media Manager"),
            goal=cfg.get(
                "goal",
                "Reformat content for social platforms without losing the voice",
            ),
            backstory=cfg.get(
                "backstory",
                "You adapt Legacy AI content for LinkedIn and X. Professional "
                "but human. No 'thrilled to announce'. Just talk.",
            ),
            llm=LLM(
                model=self.config.default_model,
                temperature=self.config.writer_temperature,
            ),
            verbose=self.config.verbose,
        )

    def _create_seo_specialist(self) -> Agent:
        tools = []
        try:
            if os.getenv("SERPER_API_KEY"):
                tools.append(SerperDevTool())
        except Exception:
            pass

        return Agent(
            role="SEO Specialist",
            goal="Make Legacy AI content discoverable without making it sound like SEO garbage",
            backstory=(
                "You optimize content for search engines while preserving the "
                "authentic Legacy AI voice. You suggest keywords, meta descriptions, "
                "and title variants. You NEVER stuff keywords or write clickbait. "
                "Good SEO feels invisible."
            ),
            tools=tools,
            llm=LLM(
                model=self.config.default_model,
                temperature=0.4,
            ),
            verbose=self.config.verbose,
        )

    def _create_brand_coordinator(self) -> Agent:
        cfg = self.agents_cfg.get("BRAND_COORDINATOR", {})
        return Agent(
            role=cfg.get("role", "Brand Coordinator"),
            goal=cfg.get(
                "goal",
                "Final gatekeeper — ensure everything sounds like Legacy AI",
            ),
            backstory=cfg.get(
                "backstory",
                "You are the last line of defense. You read every piece and ask: "
                "Would a guy in the woods with a Pink Floyd shirt say this? "
                "If no, send it back. Flag corporate speak. Encourage authenticity.",
            ),
            llm=LLM(
                model=self.config.default_model,
                temperature=self.config.reviewer_temperature,
            ),
            verbose=self.config.verbose,
        )

    # =========================================================================
    # FLOW METHODS
    # =========================================================================

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> MarketingState:
        """ENTRY POINT — validate inputs and set up state."""
        try:
            self.state.task_id = inputs.get(
                "task_id",
                f"mkt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )
            self.state.topic = inputs.get("topic", "")
            self.state.content_type = inputs.get("content_type", "blog")
            self.state.target_platforms = inputs.get(
                "target_platforms", ["linkedin", "twitter"]
            )
            self.state.raw_notes = inputs.get("raw_notes", "")
            self.state.reference_docs = inputs.get("reference_docs", "")
            self.state.created_at = datetime.utcnow().isoformat()
            self.state.status = "initialized"
            self.state.progress = 5.0

            self.analytics.start(self.state.task_id)
            logger.info(
                "Marketing flow initialized",
                task_id=self.state.task_id,
                topic=self.state.topic,
            )
            return self.state

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state.status = "error"
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("initialize")
    async def strategize(self, state: MarketingState) -> MarketingState:
        """STEP 2 — Content Strategist plans the content."""
        if self.state.status == "error":
            return self.state

        try:
            self.state.status = "strategizing"
            strategist = self._create_content_strategist()

            task = Task(
                description=f"""
Plan a content piece for Legacy AI.

TOPIC: {self.state.topic}
CONTENT TYPE: {self.state.content_type}
TARGET PLATFORMS: {", ".join(self.state.target_platforms)}
RAW NOTES FROM FOUNDER: {self.state.raw_notes or "None provided"}
REFERENCE MATERIAL: {self.state.reference_docs[:2000] or "None"}

Create a content plan with:
1. ANGLE — what's the hook? What makes someone stop scrolling?
2. KEY POINTS — 3-5 things the piece must cover
3. TONE GUIDANCE — specific voice notes for the writer
4. CALL TO ACTION — what should the reader do after?
5. DISTRIBUTION NOTES — platform-specific considerations

Remember: Legacy AI is one person in Indiana who builds open-source AI tools
out of spite. The audience is developers, not executives.
""",
                expected_output="Content strategy document with angle, key points, tone, CTA, distribution",
                agent=strategist,
            )

            crew = Crew(
                agents=[strategist],
                tasks=[task],
                process=Process.sequential,
                verbose=self.config.verbose,
            )
            result = await crew.kickoff_async()

            self.state.content_strategy = str(result)
            self.state.progress = 20.0
            self.analytics.record(cost=0.03)
            logger.info("Content strategy complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Strategy failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("strategize")
    async def write_content(self, state: MarketingState) -> MarketingState:
        """STEP 3 — Content Writer drafts the long-form piece."""
        try:
            self.state.status = "writing"
            writer = self._create_content_writer()

            task = Task(
                description=f"""
Write a {self.state.content_type} for Legacy AI.

CONTENT STRATEGY:
{self.state.content_strategy}

STYLE GUIDE (follow this exactly):
{self.style_guide[:3000]}

TOPIC: {self.state.topic}
RAW NOTES: {self.state.raw_notes or "Use the strategy as your guide"}

RULES:
- Write in the Legacy AI voice. Conversational, honest, self-deprecating but confident.
- Use parenthetical asides for humor.
- Reference Brown County Indiana, coffee, 2 AM commits, Bella the cat when natural.
- NO corporate speak. NO "thrilled to announce". NO "leveraging synergies".
- Use "Or:" subtitle format for headers.
- Final test: "Would a guy in the woods with a Pink Floyd shirt say this?"

{f"REVISION NOTES (address these): {self.state.brand_review_notes}" if self.state.revision_count > 0 else ""}
""",
                expected_output=f"Complete {self.state.content_type} in Legacy AI voice, ready for review",
                agent=writer,
            )

            crew = Crew(
                agents=[writer],
                tasks=[task],
                process=Process.sequential,
                verbose=self.config.verbose,
            )
            result = await crew.kickoff_async()

            self.state.long_form_draft = str(result)
            self.state.progress = 40.0
            self.analytics.record(cost=0.05)
            logger.info("Content writing complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Writing failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("write_content")
    async def create_social_posts(self, state: MarketingState) -> MarketingState:
        """STEP 4 — Social Media Manager creates platform-specific posts."""
        try:
            self.state.status = "creating_social"
            social_mgr = self._create_social_media_manager()

            task = Task(
                description=f"""
Create social media posts based on this content:

LONG-FORM CONTENT:
{self.state.long_form_draft[:3000]}

TARGET PLATFORMS: {", ".join(self.state.target_platforms)}

For each platform, create a post that:

LINKEDIN:
- Professional but human. Same ideas, slightly less profanity.
- Hook in the first line. Personal story over announcement.
- 150-300 words. End with a question or CTA.

TWITTER/X:
- Punchy. One core idea. Under 280 chars for main tweet.
- Optional: 3-5 tweet thread version for longer pieces.
- No hashtags unless ironic.

GITHUB (if applicable):
- Release notes style. What changed, why it matters.

ALL PLATFORMS:
- NO "thrilled to announce", "humbled to share", "excited to"
- Replace with: "Look, here's the thing." or just start talking.
- Sound like a real person, not a social media intern.
""",
                expected_output="Social media posts for each target platform, clearly labeled",
                agent=social_mgr,
            )

            crew = Crew(
                agents=[social_mgr],
                tasks=[task],
                process=Process.sequential,
                verbose=self.config.verbose,
            )
            result = await crew.kickoff_async()

            # Parse into platform dict
            result_text = str(result)
            for platform in self.state.target_platforms:
                self.state.social_posts[platform] = result_text

            self.state.progress = 55.0
            self.analytics.record(cost=0.03)
            logger.info("Social posts created", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Social post creation failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("create_social_posts")
    async def seo_optimize(self, state: MarketingState) -> MarketingState:
        """STEP 5 — SEO Specialist suggests discoverability improvements."""
        try:
            self.state.status = "optimizing_seo"
            seo = self._create_seo_specialist()

            task = Task(
                description=f"""
Optimize this content for search discoverability.

CONTENT:
{self.state.long_form_draft[:3000]}

TOPIC: {self.state.topic}

Provide:
1. 5-10 target keywords (long-tail preferred)
2. SEO-optimized title options (3 variants — must still sound human, not clickbait)
3. Meta description (155 chars max, in Legacy AI voice)
4. Suggested internal linking opportunities
5. Any structural improvements for readability/SEO

CONSTRAINT: The content must still sound authentic. If an SEO suggestion
would make it sound corporate, skip it. Good SEO is invisible.
""",
                expected_output="SEO optimization suggestions: keywords, titles, meta, structure",
                agent=seo,
            )

            crew = Crew(
                agents=[seo],
                tasks=[task],
                process=Process.sequential,
                verbose=self.config.verbose,
            )
            result = await crew.kickoff_async()

            self.state.seo_suggestions = str(result)
            self.state.progress = 70.0
            self.analytics.record(cost=0.02)
            logger.info("SEO optimization complete", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("seo_optimize")
    async def brand_review(self, state: MarketingState) -> MarketingState:
        """STEP 6 — Brand Coordinator reviews everything."""
        try:
            self.state.status = "reviewing"
            reviewer = self._create_brand_coordinator()

            task = Task(
                description=f"""
Review ALL content for Legacy AI brand voice compliance.

STYLE GUIDE:
{self.style_guide[:2000]}

LONG-FORM DRAFT:
{self.state.long_form_draft[:3000]}

SOCIAL POSTS:
{str(self.state.social_posts)[:1500]}

SEO SUGGESTIONS:
{self.state.seo_suggestions[:1000]}

Your job:
1. Read every word. Ask: "Would a guy in the woods with a Pink Floyd shirt say this?"
2. Flag ANY corporate speak: "excited to", "thrilled", "leverage", "synergy", "innovative", "solution"
3. Flag fake enthusiasm or apologetic tone
4. Check for Brown County / Legacy AI authenticity markers
5. Score the content 0-100 on brand voice compliance
6. If score >= 75: APPROVE with minor notes
7. If score < 75: REVISE with specific line-by-line feedback

Return your verdict as:
VERDICT: APPROVE or REVISE
SCORE: [number]
NOTES: [specific feedback]
""",
                expected_output="Brand review verdict (APPROVE/REVISE), score, and specific notes",
                agent=reviewer,
            )

            crew = Crew(
                agents=[reviewer],
                tasks=[task],
                process=Process.sequential,
                verbose=self.config.verbose,
            )
            result = await crew.kickoff_async()

            result_text = str(result)
            self.state.brand_review_notes = result_text

            # Parse confidence from review
            if "APPROVE" in result_text.upper():
                self.state.confidence = 0.85
            else:
                self.state.confidence = 0.4

            self.state.progress = 85.0
            self.analytics.record(cost=0.02)
            logger.info(
                "Brand review complete",
                task_id=self.state.task_id,
                confidence=self.state.confidence,
            )
            return self.state

        except Exception as e:
            logger.error(f"Brand review failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    # =========================================================================
    # ROUTER — Conditional branching
    # =========================================================================

    @router(brand_review)
    def decide_next(self) -> str:
        """Route based on brand review results."""
        logger.info(
            "Routing decision",
            confidence=self.state.confidence,
            revision_count=self.state.revision_count,
            error_count=self.state.error_count,
        )

        if self.state.error_count > 3:
            return "escalate"

        if (
            self.state.confidence < 0.6
            and self.state.revision_count < self.config.max_revisions
        ):
            self.state.revision_count += 1
            logger.info("Sending back for revision", revision=self.state.revision_count)
            return "revise"

        return "approve"

    # =========================================================================
    # TERMINAL PATHS
    # =========================================================================

    @listen("approve")
    async def finalize(self, state: MarketingState) -> MarketingState:
        """SUCCESS — Package all approved content."""
        try:
            self.state.status = "finalizing"

            self.state.final_content = {
                "long_form": self.state.long_form_draft,
                "social_posts": str(self.state.social_posts),
                "seo": self.state.seo_suggestions,
                "strategy": self.state.content_strategy,
                "brand_review": self.state.brand_review_notes,
            }
            self.state.status = "completed"
            self.state.progress = 100.0
            self.state.updated_at = datetime.utcnow().isoformat()

            self.analytics.end()
            logger.info(
                "Marketing flow completed",
                task_id=self.state.task_id,
                revision_count=self.state.revision_count,
            )
            return self.state

        except Exception as e:
            logger.error(f"Finalization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state

    @listen("revise")
    async def revise_content(self, state: MarketingState) -> MarketingState:
        """REVISION — Loop back to write_content with brand feedback."""
        logger.info(
            "Revising content",
            revision=self.state.revision_count,
            task_id=self.state.task_id,
        )
        self.state.status = "revising"
        self.state.progress = 35.0
        # Flow continues to write_content via the listen chain
        return await self.write_content(state)

    @listen("escalate")
    async def escalate_to_human(self, state: MarketingState) -> MarketingState:
        """ERROR — Too many failures, need human."""
        self.state.status = "escalated"
        self.state.updated_at = datetime.utcnow().isoformat()
        logger.error(
            "Marketing flow escalated to human",
            task_id=self.state.task_id,
            error_count=self.state.error_count,
            last_error=self.state.last_error,
        )
        self.analytics.end()
        return self.state


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


async def main():
    """Run the marketing crew from the command line."""
    import json

    logger.info("Starting Legacy AI Marketing Flow")

    inputs = {
        "topic": os.getenv("TOPIC", "Why Legacy AI exists"),
        "content_type": os.getenv("CONTENT_TYPE", "blog"),
        "target_platforms": os.getenv("TARGET_PLATFORMS", "linkedin,twitter").split(
            ","
        ),
        "raw_notes": os.getenv("RAW_NOTES", ""),
        "reference_docs": os.getenv("REFERENCE_DOCS", ""),
    }

    flow = LegacyMarketingFlow()

    try:
        await flow.kickoff_async(inputs=inputs)

        print(
            json.dumps(
                {
                    "status": flow.state.status,
                    "final_content": flow.state.final_content,
                    "metrics": flow.analytics.metrics,
                },
                indent=2,
                default=str,
            )
        )

    except Exception as e:
        logger.error(f"Marketing flow failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

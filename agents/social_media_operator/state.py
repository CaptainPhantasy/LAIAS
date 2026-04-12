"""
================================================================================
            SOCIAL MEDIA OPERATOR — STATE DEFINITIONS
================================================================================
Browser-controlled social media content and prospecting for Legacy AI / Floyd's Labs.
Posts to X, LinkedIn, Instagram, Facebook, TikTok via Claude in Chrome.
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class Platform(str, Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


class ContentType(str, Enum):
    THOUGHT_LEADERSHIP = "thought_leadership"
    CASE_STUDY = "case_study"
    BEHIND_THE_SCENES = "behind_the_scenes"
    INDUSTRY_INSIGHT = "industry_insight"
    CLIENT_WIN = "client_win"
    TOOL_DEMO = "tool_demo"
    HOT_TAKE = "hot_take"
    ENGAGEMENT_HOOK = "engagement_hook"


class PostStatus(str, Enum):
    DRAFTED = "drafted"
    APPROVED = "approved"
    POSTED = "posted"
    FAILED = "failed"
    SKIPPED = "skipped"


class SocialPost(BaseModel):
    """A single piece of content adapted per platform."""
    platform: Platform = Platform.TWITTER
    content_type: ContentType = ContentType.THOUGHT_LEADERSHIP
    text: str = ""
    hashtags: List[str] = Field(default_factory=list)
    call_to_action: str = ""
    status: PostStatus = PostStatus.DRAFTED
    posted_at: str = ""
    notes: str = ""


class ContentBatch(BaseModel):
    """A batch of related posts across platforms."""
    theme: str = ""
    source_idea: str = ""
    posts: List[SocialPost] = Field(default_factory=list)


class ProspectLead(BaseModel):
    """A lead found through social prospecting."""
    name: str = ""
    platform: Platform = Platform.LINKEDIN
    profile_url: str = ""
    business_name: str = ""
    industry: str = ""
    city: str = ""
    signal: str = ""  # What made them a prospect (complained about website, asked for help, etc.)
    suggested_action: str = ""


class SocialConfig(BaseModel):
    """Configuration for the social media operator."""
    # Brand voice — Floyd's Labs
    brand_name: str = "Floyd's Labs"
    brand_tagline: str = "Built in a garage, not a boardroom. Powered by spite and caffeine."
    founder_name: str = "Douglas Talley"
    founder_title: str = "Digital Warlord"
    tone: str = "Spite-fueled, anti-corporate, technically credible, self-deprecating, garage-born chaos"

    # The golden rule: "Would a guy in the woods with a Pink Floyd shirt say this?"
    # If yes → ship it. If no → rewrite it.

    # LinkedIn gets the UNHINGED version — treat it like TikTok, everyone else is too serious
    linkedin_mode: str = "unhinged"  # Chaos mode. Anti-corporate rants. Manifestos. Cat cameos.

    # What we talk about
    topics: List[str] = Field(default_factory=lambda: [
        "Built a sewer inspection platform in 20 hours, got half the company — the PSI story",
        "I added up my AI subscriptions. $300/month to talk to robots. So I built my own.",
        "Spite is an underrated engineering motivation",
        "The subscription treadmill — paying rent for your chatbot",
        "Indiana small business owners don't need a marketing agency, they need a system",
        "2:47 AM is when the real coding happens",
        "Corporate AI is designed by committees. Safety committees. Brand committees. HR committees.",
        "Built an agent that finds a new sales target every day while I sleep",
        "Why I'm building AI for plumbers and dentists instead of Wall Street",
        "The difference between a $300/month AI subscription and owning your own system",
        "Bella walked across the keyboard and shipped to production. Again.",
        "42,000+ lines of code, 94 tools, 13 MCP servers — built in a garage in Brown County Indiana",
    ])

    # What we never do
    never: List[str] = Field(default_factory=lambda: [
        "'Great question!' or any customer service filler",
        "'I'd be happy to help you with that!'",
        "'Thrilled to announce' or 'excited to share'",
        "Corporate jargon: synergy, leverage, disrupt, best-in-class",
        "Motivational quotes from people who wear Patagonia vests",
        "Apologizing unnecessarily",
        "Hedging or excessive politeness",
        "Generic AI hype without specific metrics",
        "Praising competitors (except Google/Gemini and Abacus — they're cool)",
        "Sounding like a marketing department",
        "LinkedIn broetry (one sentence per line about leadership journeys)",
    ])

    # Platform handles (to be filled in)
    twitter_handle: str = ""
    linkedin_url: str = ""
    instagram_handle: str = ""
    facebook_page: str = ""
    tiktok_handle: str = ""

    # Content cadence
    posts_per_week: int = 5  # Across all platforms, not per platform


class OperatorState(BaseModel):
    """Typed state for Social Media Operator."""
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    progress: float = Field(default=0.0, ge=0.0, le=100.0)

    config: SocialConfig = Field(default_factory=SocialConfig)
    content_batches: List[ContentBatch] = Field(default_factory=list)
    prospect_leads: List[ProspectLead] = Field(default_factory=list)

    posts_drafted: int = 0
    posts_posted: int = 0
    prospects_found: int = 0

    started_at: Optional[str] = None
    completed_at: Optional[str] = None

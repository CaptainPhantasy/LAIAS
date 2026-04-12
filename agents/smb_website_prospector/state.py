"""
================================================================================
            SMB WEBSITE PROSPECTOR — STATE DEFINITIONS
================================================================================
Typed state for the automated local business website analysis and outreach
pipeline. Finds local businesses, analyzes their sites, sends reports with
service offers.
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class ProspectorPhase(str, Enum):
    INITIALIZE = "initialize"
    DISCOVER = "discover"
    ANALYZE = "analyze"
    DRAFT_OUTREACH = "draft_outreach"
    COMPILE_REPORT = "compile_report"
    COMPLETE = "complete"
    ERROR = "error"


class ProspectStatus(str, Enum):
    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    OUTREACH_DRAFTED = "outreach_drafted"
    SENT = "sent"
    RESPONDED = "responded"
    CONVERTED = "converted"
    SKIPPED = "skipped"


class SiteIssue(BaseModel):
    """A single issue found during site analysis."""
    category: str = ""          # SEO, Performance, Mobile, Security, Content, Design
    severity: str = "medium"    # critical, high, medium, low
    finding: str = ""
    recommendation: str = ""


class BusinessProspect(BaseModel):
    """A local business prospect."""
    business_name: str = ""
    website_url: str = ""
    email: str = ""
    phone: str = ""
    industry: str = ""
    city: str = ""
    state: str = "IN"
    status: ProspectStatus = ProspectStatus.DISCOVERED

    # Analysis results
    site_issues: List[SiteIssue] = Field(default_factory=list)
    overall_score: int = 0      # 0-100
    critical_count: int = 0
    high_count: int = 0
    analysis_summary: str = ""

    # Outreach
    outreach_email: str = ""
    report_attachment: str = ""
    notes: str = ""


class ProspectorConfig(BaseModel):
    """Pipeline configuration."""
    target_cities: List[str] = Field(
        default_factory=lambda: [
            "Bloomington", "Columbus", "Nashville",
            "Seymour", "Franklin",
        ]
    )
    target_industries: List[str] = Field(
        default_factory=lambda: [
            "plumbing", "HVAC", "electrician", "roofing",
            "landscaping", "auto repair", "dental", "salon",
            "restaurant", "cleaning service", "pest control",
            "home inspection", "painting", "flooring",
        ]
    )
    max_prospects_per_run: int = 15

    # Pricing tiers baked into the outreach
    diy_report_price: str = "$100"
    done_for_you_price: str = "$300"
    monthly_retainer: str = "$100/month"
    retainer_hours: str = "2 hours"

    # Sender info
    sender_name: str = "Douglas Talley"
    sender_title: str = "Founder"
    sender_company: str = "Legacy AI"
    sender_email: str = "douglas.talley@legacyai.space"
    sender_phone: str = "(812) 345-6789"
    sender_website: str = "legacyai.space"


class ProspectorState(BaseModel):
    """Typed state for SMB Website Prospector pipeline."""

    task_id: str = Field(default="", description="Unique pipeline run identifier")
    status: str = Field(default="pending")
    phase: ProspectorPhase = Field(default=ProspectorPhase.INITIALIZE)
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    config: ProspectorConfig = Field(default_factory=ProspectorConfig)
    prospects: List[BusinessProspect] = Field(default_factory=list)
    analyzed_prospects: List[BusinessProspect] = Field(default_factory=list)
    outreach_ready: List[BusinessProspect] = Field(default_factory=list)

    # Counters
    sites_discovered: int = 0
    sites_analyzed: int = 0
    outreach_drafted: int = 0
    report_output: str = ""

    started_at: Optional[str] = None
    completed_at: Optional[str] = None

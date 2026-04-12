"""
================================================================================
                PSI REALTOR PIPELINE — STATE DEFINITIONS
================================================================================
Typed state, enums, and data models for the realtor outreach pipeline.
Follows Godzilla pattern: Pydantic BaseModel with typed fields.
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class PipelinePhase(str, Enum):
    """Pipeline execution phases."""
    INITIALIZE = "initialize"
    RESEARCH = "research"
    QUALIFY = "qualify"
    DRAFT_OUTREACH = "draft_outreach"
    CRM_SYNC = "crm_sync"
    FOLLOWUP_CHECK = "followup_check"
    REPORT = "report"
    COMPLETE = "complete"
    ERROR = "error"


class LeadStatus(str, Enum):
    """Realtor lead lifecycle status."""
    IDENTIFIED = "identified"
    RESEARCHED = "researched"
    QUALIFIED = "qualified"
    OUTREACH_DRAFTED = "outreach_drafted"
    OUTREACH_SENT = "outreach_sent"
    FOLLOWUP_NEEDED = "followup_needed"
    RESPONDED = "responded"
    DEAL_CREATED = "deal_created"
    DISQUALIFIED = "disqualified"


class RealtorLead(BaseModel):
    """A single realtor prospect."""
    name: str = ""
    email: str = ""
    phone: str = ""
    brokerage: str = ""
    city: str = ""
    recent_listings: List[str] = Field(default_factory=list)
    specialties: List[str] = Field(default_factory=list)
    status: LeadStatus = LeadStatus.IDENTIFIED
    outreach_draft: str = ""
    followup_draft: str = ""
    hubspot_contact_id: str = ""
    hubspot_deal_id: str = ""
    notes: str = ""
    last_contacted: Optional[str] = None
    response_received: bool = False


class PipelineConfig(BaseModel):
    """Configuration for a pipeline run."""
    target_cities: List[str] = Field(
        default_factory=lambda: [
            "Indianapolis", "Carmel", "Fishers", "Noblesville",
            "Westfield", "Zionsville", "Brownsburg", "Avon",
            "Plainfield", "Greenwood", "Franklin", "Greenfield"
        ]
    )
    max_leads_per_run: int = 20
    followup_days: int = 5
    outreach_sender: str = "sales@precisionsewerinspection.com"
    company_phone: str = "(317) 620-3858"
    booking_url: str = "https://www.precisionsewerinspections.com/contact"
    pricing_url: str = "https://www.precisionsewerinspections.com/pricing"
    inspection_price: str = "$159"
    volume_discount_note: str = "We offer prepaid bundles for brokerages — 10+ scopes with per-scope discounts and priority scheduling."


class RealtorPipelineState(BaseModel):
    """Typed state for PSI Realtor Pipeline."""

    # Core tracking
    task_id: str = Field(default="", description="Unique pipeline run identifier")
    status: str = Field(default="pending", description="Current execution status")
    phase: PipelinePhase = Field(default=PipelinePhase.INITIALIZE)
    error_count: int = Field(default=0, description="Number of errors encountered")
    last_error: Optional[str] = Field(default=None, description="Most recent error message")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Result confidence score")

    # Pipeline data
    config: PipelineConfig = Field(default_factory=PipelineConfig)
    leads: List[RealtorLead] = Field(default_factory=list)
    qualified_leads: List[RealtorLead] = Field(default_factory=list)
    outreach_drafts: List[Dict[str, Any]] = Field(default_factory=list)
    crm_synced: List[str] = Field(default_factory=list)
    followups_needed: List[str] = Field(default_factory=list)

    # Results
    leads_researched: int = 0
    leads_qualified: int = 0
    outreach_drafted: int = 0
    crm_contacts_created: int = 0
    deals_created: int = 0
    report_output: str = ""

    # Timestamps
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

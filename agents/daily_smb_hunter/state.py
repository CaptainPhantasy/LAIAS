"""
================================================================================
            DAILY SMB HUNTER — STATE DEFINITIONS
================================================================================
Runs once daily at 7 PM. Finds one SMB in the Southport IN area, analyzes them,
designs the exact agent solution that guarantees 10%+ revenue increase, builds
the agent, and packages everything Ryan needs to close the deal.
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class HunterPhase(str, Enum):
    INITIALIZE = "initialize"
    HUNT = "hunt"
    DEEP_RESEARCH = "deep_research"
    SOLUTION_DESIGN = "solution_design"
    AGENT_BUILD = "agent_build"
    SALES_PACKAGE = "sales_package"
    COMPLETE = "complete"
    ERROR = "error"


class RevenueStrategy(str, Enum):
    INCREASE_LEADS = "increase_leads"
    REDUCE_CHURN = "reduce_churn"
    UPSELL_EXISTING = "upsell_existing"
    CUT_COSTS = "cut_costs"
    IMPROVE_CONVERSION = "improve_conversion"
    EXPAND_REACH = "expand_reach"


class OwnerProfile(BaseModel):
    """Everything we can find about the business owner."""
    name: str = ""
    title: str = ""
    linkedin: str = ""
    background: str = ""
    interests: str = ""
    communication_style: str = ""
    pain_points: List[str] = Field(default_factory=list)
    motivators: List[str] = Field(default_factory=list)


class BusinessTarget(BaseModel):
    """Complete intelligence package on the target business."""
    business_name: str = ""
    industry: str = ""
    address: str = ""
    city: str = "Southport"
    state: str = "IN"
    phone: str = ""
    email: str = ""
    website: str = ""
    google_rating: str = ""
    review_count: int = 0
    estimated_employees: int = 0
    estimated_annual_revenue: str = ""
    years_in_business: str = ""
    competitors: List[str] = Field(default_factory=list)
    owner: OwnerProfile = Field(default_factory=OwnerProfile)

    # Analysis
    current_strengths: List[str] = Field(default_factory=list)
    current_weaknesses: List[str] = Field(default_factory=list)
    revenue_opportunities: List[str] = Field(default_factory=list)
    website_score: int = 0
    online_presence_score: int = 0
    automation_readiness: str = ""  # low, medium, high


class SolutionSpec(BaseModel):
    """The designed agent solution for the target."""
    solution_name: str = ""
    solution_type: str = ""  # single_agent, multi_agent, workflow
    revenue_strategy: str = ""
    projected_annual_impact: str = ""
    projected_roi_percentage: str = ""
    how_it_works: str = ""
    agent_description: str = ""
    agent_code_path: str = ""

    # Pricing for the client
    setup_fee: str = ""
    monthly_fee: str = ""
    roi_timeline: str = ""


class SalesPackage(BaseModel):
    """Everything Ryan needs to close the deal."""
    one_liner: str = ""
    elevator_pitch: str = ""
    discovery_questions: List[str] = Field(default_factory=list)
    objection_handlers: Dict[str, str] = Field(default_factory=dict)
    ad_copy: str = ""
    email_intro: str = ""
    voicemail_script: str = ""
    leave_behind_summary: str = ""
    competitive_advantage: str = ""
    urgency_hook: str = ""
    closing_line: str = ""


class HunterConfig(BaseModel):
    """Daily hunter configuration."""
    target_area: str = "Southport, Indiana"
    search_radius: str = "Southport, Indianapolis south side, Greenwood, Beech Grove"
    min_revenue_impact: str = "10%"
    industries_priority: List[str] = Field(
        default_factory=lambda: [
            "plumbing", "HVAC", "electrician", "roofing", "landscaping",
            "auto repair", "dental", "veterinary", "salon", "barbershop",
            "restaurant", "pizza", "cleaning service", "pest control",
            "home inspection", "painting", "flooring", "appliance repair",
            "locksmith", "towing", "storage", "daycare", "fitness",
            "martial arts", "tutoring", "photography", "catering",
        ]
    )
    exclude_previously_targeted: bool = True
    history_file: str = "/Volumes/SanDisk1Tb/LAIAS_AGENT_OUTPUT/daily_smb_hunter/_hunt_history.json"

    # Sales team info
    salesperson_name: str = "Ryan"
    salesperson_phone: str = ""
    company_name: str = "Legacy AI"
    company_website: str = "legacyai.space"
    company_phone: str = "(812) 345-6789"

    # Pricing defaults
    default_setup_low: str = "$300"
    default_setup_high: str = "$2,000"
    default_monthly_low: str = "$100"
    default_monthly_high: str = "$500"


class HunterState(BaseModel):
    """Typed state for Daily SMB Hunter."""

    task_id: str = Field(default="")
    status: str = Field(default="pending")
    phase: HunterPhase = Field(default=HunterPhase.INITIALIZE)
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    config: HunterConfig = Field(default_factory=HunterConfig)
    target: BusinessTarget = Field(default_factory=BusinessTarget)
    solution: SolutionSpec = Field(default_factory=SolutionSpec)
    sales_package: SalesPackage = Field(default_factory=SalesPackage)

    # The generated agent code
    generated_agent_code: str = ""
    generated_agent_path: str = ""

    # Run metadata
    hunt_date: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

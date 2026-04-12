#!/usr/bin/env python3
"""
================================================================================
            INDIANA SMB CLIENT ACQUISITION AGENT
            "Your AI-Powered Business Development Assistant"
================================================================================

An elite 6-agent system designed specifically for solo developers targeting
Indiana SMBs. Focuses on lead generation, relationship building, and deal closure
for custom software solutions, website design, and AI integration services.

Author: LAIAS Agent Generator
Date: March 2026
================================================================================
"""

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start
from crewai_tools import ScrapeWebsiteTool, SerperDevTool, FileReadTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog
import os
import json

logger = structlog.get_logger()

# =============================================================================
# STATE MODEL
# =============================================================================


class BusinessDevState(BaseModel):
    """State for the Indiana SMB Client Acquisition Agent."""
    
    # Identity & Status
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    progress: float = Field(default=0.0)
    current_phase: str = Field(default="initialization")
    
    # Error Handling
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    
    # Business Development Data
    target_industries: List[str] = Field(default_factory=lambda: [
        "Healthcare", "Manufacturing", "Legal", "Agriculture", 
        "Professional Services", "Retail", "Education"
    ])
    target_geography: str = Field(default="Indiana (Brown County, Columbus, Bloomington, Indianapolis, 100-mile radius)")
    lead_generation_results: Dict[str, Any] = Field(default_factory=dict)
    prospect_profiles: List[Dict[str, Any]] = Field(default_factory=list)
    outreach_campaigns: List[Dict[str, Any]] = Field(default_factory=list)
    follow_up_schedule: List[Dict[str, Any]] = Field(default_factory=list)
    qualified_leads: List[Dict[str, Any]] = Field(default_factory=list)
    closed_deals: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Content & Marketing
    marketing_content: Dict[str, str] = Field(default_factory=dict)
    social_media_posts: List[str] = Field(default_factory=list)
    case_study_materials: List[str] = Field(default_factory=list)
    
    # Metrics & Analytics
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


# =============================================================================
# FLOW CLASS
# =============================================================================


class IndianaSMBBusinessDevFlow(Flow[BusinessDevState]):
    """
    Elite 6-agent business development system for Indiana SMBs.
    Specialized for custom software, website design, and AI integration.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = self._get_llm()
        self.scraper = ScrapeWebsiteTool()
        self.search_tool = SerperDevTool() if os.getenv("SERPER_API_KEY") else None
        self.output_dir = Path("/Volumes/Storage/LAIAS/output/business_dev")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics
        self.state.metrics = {
            "leads_generated": 0,
            "outreach_attempts": 0,
            "responses_received": 0,
            "meetings_scheduled": 0,
            "deals_closed": 0,
            "revenue_generated": 0
        }

    def _get_llm(self) -> LLM:
        """Get the configured LLM routed through Portkey gateway."""
        return LLM(
            model=os.getenv("DEFAULT_MODEL", "gpt-4o"),
            base_url="https://api.portkey.ai/v1",
            api_key=os.getenv("PORTKEY_API_KEY", ""),
        )

    def _save_results(self, stage: str, data: Any):
        """Save results to file."""
        filename = f"{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved {stage} results", path=str(filepath))

    # =========================================================================
    # PHASE 1: MARKET RESEARCH & LEAD IDENTIFICATION
    # =========================================================================
    
    @start()
    async def research_market(self) -> BusinessDevState:
        """Research Indiana SMB market and identify potential leads."""
        if not self.state.task_id:
            self.state.task_id = f"smb_dev_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.state.created_at = datetime.utcnow().isoformat()
        self.state.status = "researching"
        self.state.progress = 5.0
        self.state.current_phase = "market_research"
        
        logger.info("Phase 1: Market Research & Lead Identification", task_id=self.state.task_id)
        
        researcher = Agent(
            role="Indiana SMB Market Research Specialist",
            goal="Identify high-value prospects in Indiana SMB market for custom software, website design, and AI integration",
            backstory="""You are an expert in Indiana SMB market research with deep knowledge of regional business ecosystems.
            You specialize in identifying companies that would benefit from custom software solutions, modern websites, and AI integration.
            You understand that the best prospects are those experiencing growth pains, manual processes, or competitive pressure.
            
            Your target industries are: Healthcare, Manufacturing, Legal, Agriculture, Professional Services, Retail, Education.
            Your geography is: Indiana, especially Brown County, Columbus, Bloomington, Indianapolis, and 100-mile radius.
            
            You look for signs of growth, recent investments, expansion announcements, or operational challenges that suggest
            a need for technology solutions.""",
            llm=self.llm,
            tools=[self.scraper, self.search_tool] if self.search_tool else [self.scraper],
            verbose=True,
            max_iter=25,
        )
        
        task = Task(
            description=f"""
            Conduct comprehensive market research to identify high-value prospects in Indiana SMB market.
            
            TARGET GEOGRAPHY: {self.state.target_geography}
            TARGET INDUSTRIES: {', '.join(self.state.target_industries)}
            
            RESEARCH FOCUS:
            1. Companies showing signs of growth (expansion announcements, new hires, funding rounds)
            2. Businesses with outdated technology or manual processes
            3. Organizations facing competitive pressure or operational challenges
            4. Companies that have recently received awards, recognition, or media coverage
            5. Businesses expanding into new markets or launching new products
            
            RESEARCH SOURCES:
            - Local business journals and publications
            - Chamber of Commerce directories
            - Industry association websites
            - LinkedIn company pages
            - News articles and press releases
            - Government databases and reports
            - Competitor analysis
            
            DELIVERABLES:
            1. List of 50-100 high-potential prospects with:
               - Company name and description
               - Industry and size
               - Key decision makers and contact info
               - Recent developments indicating need for technology solutions
               - Potential value proposition fit
            2. Market analysis report with:
               - Industry trends affecting target sectors
               - Common pain points in each industry
               - Technology adoption patterns
               - Competitive landscape
            3. Prioritized prospect list ranked by likelihood to convert
            """,
            expected_output="Comprehensive market research report with prioritized prospect list",
            agent=researcher,
        )
        
        crew = Crew(
            agents=[researcher], 
            tasks=[task], 
            process=Process.sequential, 
            verbose=True
        )
        result = await crew.kickoff_async()
        
        research_output = str(result)
        self.state.lead_generation_results = {
            "raw_output": research_output,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.progress = 20.0
        
        # Parse prospects from research
        # In a real implementation, this would involve parsing the research output
        # For now, we'll simulate with a sample structure
        self.state.prospect_profiles = [
            {
                "company_name": "Sample Business",
                "industry": "Manufacturing",
                "size": "50-200 employees",
                "location": "Indianapolis",
                "decision_maker": "CTO Jane Smith",
                "email": "jane.smith@sample.com",
                "phone": "(317) 555-0123",
                "pain_points": ["Manual inventory tracking", "Outdated ERP system"],
                "potential_value": "$50K-$100K project"
            }
        ]
        
        self._save_results("market_research", self.state.lead_generation_results)
        logger.info("Phase 1 complete: Market Research", prospects=len(self.state.prospect_profiles))
        return self.state

    # =========================================================================
    # PHASE 2: CONTENT CREATION & PERSONALIZATION
    # =========================================================================
    
    @listen("research_market")
    async def create_personalized_content(self) -> BusinessDevState:
        """Create personalized content for each prospect."""
        if self.state.error_count > 2:
            return self.state
            
        self.state.status = "creating_content"
        self.state.progress = 25.0
        self.state.current_phase = "content_creation"
        logger.info("Phase 2: Content Creation & Personalization")
        
        content_creator = Agent(
            role="Personalized Content Specialist",
            goal="Create compelling, personalized content for each prospect highlighting value of custom software, websites, and AI integration",
            backstory="""You are a master of personalized content creation with deep understanding of Indiana SMB challenges.
            You craft messages that resonate with specific industries and business situations. You know that generic outreach
            rarely converts, but personalized content addressing specific pain points gets attention.
            
            You understand that for custom software, the value is in efficiency gains and competitive advantage.
            For website design, it's about modern presence and customer acquisition.
            For AI integration, it's about staying ahead of the curve and automating repetitive tasks.
            
            Your content is authentic, specific, and valuable - never salesy or generic.""",
            llm=self.llm,
            verbose=True,
            max_iter=25,
        )
        
        task = Task(
            description=f"""
            Create personalized content for each prospect identified in the research phase.
            
            PROSPECT DATA:
            {json.dumps(self.state.prospect_profiles[:5], indent=2)}  # Limit to first 5 for example
            
            CONTENT REQUIREMENTS:
            1. Personalized outreach emails (3 variations per prospect)
            2. LinkedIn connection requests with personalized notes
            3. Follow-up sequences (3 touches per prospect)
            4. Value proposition statements tailored to each industry
            5. Case study examples relevant to each prospect's situation
            
            EMAIL TEMPLATES SHOULD:
            - Address specific pain points identified in research
            - Reference recent company developments
            - Highlight relevant success stories
            - Include clear, low-pressure CTA
            - Feel authentic and human, not salesy
            
            LINKEDIN MESSAGES SHOULD:
            - Be concise and relevant
            - Reference mutual connections or interests
            - Offer value upfront
            - Lead to email follow-up
            
            CASE STUDIES SHOULD:
            - Mirror the prospect's situation
            - Quantify results achieved
            - Include testimonials from similar businesses
            - Demonstrate expertise in their industry
            
            FORMAT: Provide content in structured format suitable for CRM import.
            """,
            expected_output="Personalized content pack for each prospect with emails, LinkedIn messages, and case studies",
            agent=content_creator,
        )
        
        crew = Crew(
            agents=[content_creator], 
            tasks=[task], 
            process=Process.sequential, 
            verbose=True
        )
        result = await crew.kickoff_async()
        
        content_output = str(result)
        self.state.marketing_content = {
            "personalized_outreach": content_output,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.progress = 40.0
        
        self._save_results("personalized_content", self.state.marketing_content)
        logger.info("Phase 2 complete: Content Creation", content_pieces=len(self.state.prospect_profiles)*3)
        return self.state

    # =========================================================================
    # PHASE 3: OUTREACH CAMPAIGN EXECUTION
    # =========================================================================
    
    @listen("create_personalized_content")
    async def execute_outreach_campaign(self) -> BusinessDevState:
        """Execute multi-channel outreach campaign."""
        if self.state.error_count > 2:
            return self.state
            
        self.state.status = "executing_outreach"
        self.state.progress = 45.0
        self.state.current_phase = "outreach_execution"
        logger.info("Phase 3: Outreach Campaign Execution")
        
        outreach_specialist = Agent(
            role="Multi-Channel Outreach Specialist",
            goal="Execute systematic outreach campaign using multiple channels to maximize response rates",
            backstory="""You are an expert in multi-channel outreach campaigns with proven success in B2B lead generation.
            You understand that different prospects prefer different communication channels and that consistent follow-up
            is essential for conversion.
            
            Your approach is strategic and respectful - you provide value in every touchpoint and respect busy schedules.
            You track response rates by channel and adjust tactics accordingly.
            
            You know that the first touch rarely converts, but consistent follow-up with valuable content builds trust
            and moves prospects toward consideration.""",
            llm=self.llm,
            verbose=True,
            max_iter=25,
        )
        
        task = Task(
            description=f"""
            Design and execute a systematic multi-channel outreach campaign.
            
            PROSPECT DATA:
            {json.dumps(self.state.prospect_profiles[:10], indent=2)}  # Limit to first 10 for example
            
            PERSONALIZED CONTENT:
            {self.state.marketing_content.get('personalized_outreach', '')[:2000]}  # Truncate for example
            
            CAMPAIGN REQUIREMENTS:
            1. Multi-channel approach: Email, LinkedIn, Phone (where appropriate)
            2. Touch sequence: Initial contact → Value-add touch → Follow-up → Final attempt
            3. Timing: Staggered schedule to avoid appearing spammy
            4. Tracking: Response rates, engagement levels, interest indicators
            5. Qualification: Criteria for moving prospects to next stage
            
            EXECUTION PLAN:
            - Week 1: Initial outreach to 20 prospects
            - Week 2: First follow-up to non-responders, value-add to responders
            - Week 3: Second follow-up to interested prospects, schedule calls
            - Week 4: Final attempts, nurture remaining prospects
            
            CHANNEL SPECIFICS:
            Email: Professional, personalized, clear value proposition
            LinkedIn: Concise, relationship-building, value-focused
            Phone: Warm introduction, brief, appointment-setting
            
            QUALIFICATION CRITERIA:
            - Budget availability (>$25K for custom projects)
            - Authority (decision maker contacted)
            - Need (identified pain points)
            - Timeline (project within 3-6 months)
            
            DELIVERABLES:
            - Outreach calendar with scheduled activities
            - Response tracking spreadsheet
            - Qualified lead pipeline
            - Engagement metrics by channel
            """,
            expected_output="Complete outreach campaign plan with calendar, tracking sheets, and qualification criteria",
            agent=outreach_specialist,
        )
        
        crew = Crew(
            agents=[outreach_specialist], 
            tasks=[task], 
            process=Process.sequential, 
            verbose=True
        )
        result = await crew.kickoff_async()
        
        outreach_output = str(result)
        self.state.outreach_campaigns = [{
            "campaign_plan": outreach_output,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "executing"
        }]
        self.state.progress = 60.0
        
        self._save_results("outreach_campaign", self.state.outreach_campaigns)
        logger.info("Phase 3 complete: Outreach Campaign", prospects_contacted=len(self.state.prospect_profiles))
        return self.state

    # =========================================================================
    # PHASE 4: RELATIONSHIP BUILDING & QUALIFICATION
    # =========================================================================
    
    @listen("execute_outreach_campaign")
    async def build_relationships_qualify_leads(self) -> BusinessDevState:
        """Build relationships with engaged prospects and qualify leads."""
        if self.state.error_count > 2:
            return self.state
            
        self.state.status = "building_relationships"
        self.state.progress = 65.0
        self.state.current_phase = "relationship_building"
        logger.info("Phase 4: Relationship Building & Lead Qualification")
        
        relationship_builder = Agent(
            role="Relationship Building & Lead Qualification Specialist",
            goal="Build trust with engaged prospects and qualify them based on budget, authority, need, and timeline",
            backstory="""You excel at building authentic relationships with prospects and qualifying them effectively.
            You understand that trust is built through consistent value delivery, not aggressive selling.
            
            You use consultative questioning to uncover true needs and pain points.
            You assess budget, authority, need, and timeline systematically.
            You provide value in every interaction through insights, resources, or introductions.
            
            Your qualification process is thorough but respectful of time.
            You know when to advance prospects and when to nurture them further.""",
            llm=self.llm,
            verbose=True,
            max_iter=25,
        )
        
        task = Task(
            description=f"""
            Develop relationships with engaged prospects and qualify them using BANT framework.
            
            ENGAGED PROSPECTS:
            {json.dumps([p for p in self.state.prospect_profiles if p.get('engaged', False)][:10], indent=2)}
            
            QUALIFICATION FRAMEWORK (BANT):
            Budget: Confirm available budget for custom software/website/AI projects ($25K+ typical)
            Authority: Verify decision-making authority or access to decision makers
            Need: Validate specific pain points and business impact
            Timeline: Establish realistic project timeline (3-6 months typical)
            
            RELATIONSHIP BUILDING ACTIVITIES:
            1. Discovery calls to understand specific challenges
            2. Value demonstrations (case studies, portfolio review)
            3. Industry insights sharing
            4. Referral requests to expand network
            5. Thought leadership content sharing
            
            QUALIFICATION PROCESS:
            - Needs assessment questionnaire
            - Budget discussion techniques
            - Decision maker identification
            - Timeline validation
            - Competition awareness
            - Internal champion development
            
            NURTURING STRATEGY:
            For prospects not ready now but showing interest:
            - Regular value-add communications
            - Invitation to webinars/events
            - Industry reports sharing
            - Referral program participation
            
            DELIVERABLES:
            - Qualified lead profiles with BANT scores
            - Relationship strength indicators
            - Next steps for each qualified lead
            - Nurture campaign for unqualified but interested prospects
            """,
            expected_output="Qualified lead profiles with BANT scores and relationship strength indicators",
            agent=relationship_builder,
        )
        
        crew = Crew(
            agents=[relationship_builder], 
            tasks=[task], 
            process=Process.sequential, 
            verbose=True
        )
        result = await crew.kickoff_async()
        
        qualification_output = str(result)
        self.state.qualified_leads = [{
            "qualification_report": qualification_output,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "qualified"
        }]
        self.state.progress = 80.0
        
        self._save_results("qualification", self.state.qualified_leads)
        logger.info("Phase 4 complete: Relationship Building", qualified_leads=len(self.state.qualified_leads))
        return self.state

    # =========================================================================
    # PHASE 5: PROPOSAL DEVELOPMENT & DEAL CLOSURE
    # =========================================================================
    
    @listen("build_relationships_qualify_leads")
    async def develop_proposals_close_deals(self) -> BusinessDevState:
        """Develop proposals and close deals with qualified leads."""
        if self.state.error_count > 2:
            return self.state
            
        self.state.status = "closing_deals"
        self.state.progress = 85.0
        self.state.current_phase = "deal_closure"
        logger.info("Phase 5: Proposal Development & Deal Closure")
        
        proposal_specialist = Agent(
            role="Proposal Development & Deal Closure Specialist",
            goal="Create compelling proposals and close deals with qualified leads for custom software, websites, and AI integration",
            backstory="""You are a master of proposal development and deal closure with deep expertise in technology solutions.
            You understand that the best proposals address specific business challenges with clear ROI and implementation plans.
            
            Your proposals are professional, detailed, and compelling.
            You include case studies, timelines, team credentials, and risk mitigation strategies.
            You handle objections proactively and close deals with confidence.
            
            You know that price is rarely the deciding factor - value, trust, and execution capability are what win deals.""",
            llm=self.llm,
            verbose=True,
            max_iter=25,
        )
        
        task = Task(
            description=f"""
            Develop compelling proposals and close deals with qualified leads.
            
            QUALIFIED LEADS DATA:
            {json.dumps(self.state.qualified_leads[:5], indent=2)}  # Limit to first 5 for example
            
            PROPOSAL REQUIREMENTS:
            1. Executive summary addressing specific business challenge
            2. Solution overview with custom software/website/AI integration details
            3. Implementation timeline with milestones
            4. Team credentials and past success stories
            5. Investment breakdown and ROI projections
            6. Risk mitigation and support plans
            7. Terms and conditions
            
            CLOSURE STRATEGY:
            - Present solutions that directly address identified pain points
            - Demonstrate clear ROI and business impact
            - Handle common objections proactively
            - Create urgency without being pushy
            - Secure commitment and next steps
            
            DEAL TYPES:
            Custom Software Solutions: $25K-$100K projects
            Website Design & Development: $10K-$50K projects  
            AI Integration Projects: $30K-$150K projects
            Ongoing Support & Maintenance: Monthly retainers
            
            NEGOTIATION TACTICS:
            - Focus on value delivered vs. price
            - Bundle services for better economics
            - Offer phased implementation to reduce risk
            - Include performance guarantees
            - Provide flexible payment terms
            
            DELIVERABLES:
            - Detailed proposals for each qualified lead
            - Negotiation strategies for each opportunity
            - Contract templates for different service types
            - Closing scripts and objection handlers
            - Post-closure onboarding plans
            """,
            expected_output="Compelling proposals with negotiation strategies and contract templates",
            agent=proposal_specialist,
        )
        
        crew = Crew(
            agents=[proposal_specialist], 
            tasks=[task], 
            process=Process.sequential, 
            verbose=True
        )
        result = await crew.kickoff_async()
        
        proposal_output = str(result)
        self.state.closed_deals = [{
            "proposal_document": proposal_output,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "closed"
        }]
        self.state.progress = 95.0
        
        self._save_results("proposals", self.state.closed_deals)
        logger.info("Phase 5 complete: Proposal Development", proposals=len(self.state.closed_deals))
        return self.state

    # =========================================================================
    # PHASE 6: METRICS & OPTIMIZATION
    # =========================================================================
    
    @listen("develop_proposals_close_deals")
    async def analyze_metrics_optimize(self) -> BusinessDevState:
        """Analyze campaign metrics and optimize for future success."""
        if self.state.error_count > 2:
            return self.state
            
        self.state.status = "analyzing"
        self.state.progress = 98.0
        self.state.current_phase = "optimization"
        logger.info("Phase 6: Metrics Analysis & Optimization")
        
        analyst = Agent(
            role="Business Development Metrics Analyst",
            goal="Analyze campaign performance and optimize strategies for continued success",
            backstory="""You are an expert in analyzing business development metrics and optimizing strategies.
            You understand which activities drive the best ROI and how to scale successful approaches.
            
            You track key metrics like cost per lead, conversion rates, deal size, and sales cycle length.
            You identify patterns in successful vs. unsuccessful approaches.
            You provide actionable recommendations for continuous improvement.""",
            llm=self.llm,
            verbose=True,
            max_iter=20,
        )
        
        task = Task(
            description=f"""
            Analyze business development campaign metrics and provide optimization recommendations.
            
            CAMPAIGN DATA:
            - Leads generated: {len(self.state.prospect_profiles)}
            - Outreach attempts: {len(self.state.outreach_campaigns)}
            - Qualified leads: {len(self.state.qualified_leads)}
            - Closed deals: {len(self.state.closed_deals)}
            
            METRICS TO ANALYZE:
            1. Lead generation efficiency (cost per lead, time per lead)
            2. Conversion rates (outreach→response, response→qualified, qualified→closed)
            3. Deal values and profitability
            4. Channel effectiveness (email vs. LinkedIn vs. phone)
            5. Industry performance (which verticals convert best)
            6. Timing effectiveness (optimal days/times for outreach)
            
            OPTIMIZATION RECOMMENDATIONS:
            1. Focus areas - which activities drove best results
            2. Resource allocation - where to invest more effort
            3. Process improvements - streamline inefficient steps
            4. Tool recommendations - what would improve productivity
            5. Scaling strategies - how to increase volume while maintaining quality
            6. Retention strategies - how to turn clients into advocates
            
            REPORT FORMAT:
            - Executive summary with key findings
            - Detailed metric breakdowns
            - Actionable recommendations
            - Priority-ranked improvement initiatives
            - Success metrics for next campaign
            
            Include specific, quantifiable recommendations with expected impact.
            """,
            expected_output="Comprehensive metrics analysis with optimization recommendations",
            agent=analyst,
        )
        
        crew = Crew(
            agents=[analyst], 
            tasks=[task], 
            process=Process.sequential, 
            verbose=True
        )
        result = await crew.kickoff_async()
        
        analysis_output = str(result)
        self.state.metrics.update({
            "campaign_analysis": analysis_output,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "complete"
        })
        self.state.progress = 100.0
        self.state.status = "completed"
        self.state.completed_at = datetime.utcnow().isoformat()
        
        self._save_results("metrics_analysis", self.state.metrics)
        logger.info("Phase 6 complete: Metrics Analysis", deals_closed=len(self.state.closed_deals))
        return self.state


# =============================================================================
# MAIN EXECUTION
# =============================================================================


async def main():
    """Run the Indiana SMB Client Acquisition Agent."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              INDIANA SMB CLIENT ACQUISITION AGENT                           ║
║              "Your AI-Powered Business Development Assistant"                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Phase 1: Market Research → Identify high-value prospects                   ║
║  Phase 2: Content Creation → Personalized outreach materials               ║
║  Phase 3: Outreach Execution → Multi-channel campaign                       ║
║  Phase 4: Relationship Building → Qualify leads with BANT framework         ║
║  Phase 5: Deal Closure → Proposals and contract negotiations               ║
║  Phase 6: Metrics Analysis → Optimize for continued success                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    flow = IndianaSMBBusinessDevFlow()
    
    await flow.kickoff_async(inputs={})
    
    print("\n" + "=" * 78)
    print("INDIANA SMB BUSINESS DEVELOPMENT COMPLETE")
    print("=" * 78)
    print(f"Status     : {flow.state.status}")
    print(f"Progress   : {flow.state.progress}%")
    print(f"Prospects  : {len(flow.state.prospect_profiles)} identified")
    print(f"Qualified  : {len(flow.state.qualified_leads)} qualified")
    print(f"Deals      : {len(flow.state.closed_deals)} closed")
    print(f"Started    : {flow.state.created_at}")
    print(f"Completed  : {flow.state.completed_at}")
    print("=" * 78)
    
    return flow.state


if __name__ == "__main__":
    import asyncio
    
    asyncio.run(main())
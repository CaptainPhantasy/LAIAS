"""
================================================================================
            INDIANA SEWER SCOPE WEB DESIGN TEAM
            "Building Indiana's #1 Sewer Scoping Website"
================================================================================

                    ███████╗ ██████╗ ██╗
                    ╚══███╔╝██╔═══██╗██║
                      ███╔╝ ██║   ██║██║
                     ███╔╝  ██║   ██║██║
                    ███████╗╚██████╔╝███████╗
                    ╚══════╝ ╚═════╝ ╚══════╝

                A 6-Agent Elite Design Team Workflow
                    Production-Grade Website Design

================================================================================
ARCHITECTURE: Godzilla Pattern
FLOW: Analyze → UX Design → Visual Design → Copywriting → Tech Spec → Compile
VERSION: 1.0.0
================================================================================
"""

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import os
import json

# =============================================================================
# LOGGING
# =============================================================================

logger = structlog.get_logger()


# =============================================================================
# STATE CLASS
# =============================================================================

class WebDesignState(BaseModel):
    """State for the Web Design Team Workflow."""
    
    # Execution Identity
    task_id: str = Field(default="", description="Unique task identifier")
    project_name: str = Field(default="Indiana Sewer Scope Website")
    
    # Status Tracking
    status: str = Field(default="pending")
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    current_phase: str = Field(default="initialization")
    
    # Error Handling
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    
    # Input Data
    competitive_research: Dict[str, Any] = Field(default_factory=dict)
    business_requirements: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent Outputs (Each Specialist's Work)
    competitive_analysis: Dict[str, Any] = Field(default_factory=dict)
    ux_architecture: Dict[str, Any] = Field(default_factory=dict)
    visual_design_system: Dict[str, Any] = Field(default_factory=dict)
    conversion_copy: Dict[str, Any] = Field(default_factory=dict)
    technical_architecture: Dict[str, Any] = Field(default_factory=dict)
    
    # Final Deliverable
    website_specification: Optional[str] = Field(default=None)
    specification_path: Optional[str] = Field(default=None)
    
    # Configuration
    output_directory: str = Field(default="/Volumes/Storage/Research")
    target_market: str = Field(default="Indiana")
    industry: str = Field(default="sewer_scope_inspection")
    
    # Metadata
    created_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


# =============================================================================
# COMPETITIVE RESEARCH DATA (From Analysis)
# =============================================================================

COMPETITIVE_RESEARCH = """
# Indiana Sewer Scoping Competitive Intelligence

## TOP 5 COMPETITORS ANALYZED

### 1. Sewer Scope USA (Indianapolis)
- Website: sewerscopeusa.com
- Pricing: $200 base + $50 add-ons
- STRENGTHS: Clear pricing, online booking <2 min, 24-hour turnaround, "no upsell" positioning
- WEAKNESSES: Generic stock photos, no AI/chat, minimal content marketing
- COLOR SCHEME: Dark teal #1a5f7a, Light teal #57c5b6
- KEY VERBIAGE: "Book a sewer scope in less than 2 minutes", "We are inspectors, not contractors"

### 2. ScopeWell (Fort Wayne/Indianapolis)
- Website: scopewell.com
- Pricing: $200-$300 based on access method
- STRENGTHS: Excellent testimonials, money-back guarantee, detailed FAQ, strong SEO
- WEAKNESSES: Long single-page, keyword stuffing obvious
- COLOR SCHEME: Forest green #2d6a4f, Light green #74c69d
- KEY VERBIAGE: "Best Sewer Scope Company Near You!", "We will treat you like family"

### 3. WIN Home Inspection (Evansville)
- Website: wini.com
- STRENGTHS: Enterprise tech stack (Next.js), user segmentation, professional
- WEAKNESSES: Sewer scope buried in services, corporate feel, no pricing
- COLOR SCHEME: WIN blue #0056b3, Amber CTAs #ffc107

### 4. SLB Pipe Solutions (Multi-city)
- Website: slbpipesolutions.com
- STRENGTHS: Full-service, No-Dig certified, BBB A-rating, 50-year guarantee
- WEAKNESSES: Overwhelming navigation, camera inspection not primary
- COLOR SCHEME: Navy #1e3a5f, Coral CTAs #ee6c4d

### 5. Indiana RooterMan (Central IN)
- Website: indianarooterman.com
- STRENGTHS: Educational content, property manager focus, multi-tool approach
- WEAKNESSES: Generic branding, not specialized
- COLOR SCHEME: Blue #0055a5, Orange CTAs #ff6600

## COMPETITIVE GAPS (Opportunities)

1. NO AI CHAT - 24/7 instant answers (HIGH priority)
2. NO VIDEO CONTENT - Camera footage samples (HIGH priority)
3. NO INSTANT QUOTES - Interactive pricing calculator (MEDIUM priority)
4. NO BEFORE/AFTER - Case study gallery (MEDIUM priority)
5. NO LIVE CHAT - Real-time support (HIGH priority)

## DESIGN PATTERNS FOUND

### Common Color Schemes:
- Blue dominance (8/14 sites) - Trust, water association
- Green accents (3/14 sites) - Clean, "go" psychology
- Orange CTAs (6/14 sites) - Urgency, action

### Required Components (ALL sites have):
- Hero CTA above fold
- Phone number prominent
- Service area listing
- "No upsell" messaging
- 24-hour turnaround promise
- Testimonials

### Technology Stack:
- WordPress: 71% of sites
- Wix: 14% (small operators)
- Next.js: 7% (WIN only - enterprise)

## INDIANA-SPECIFIC INSIGHTS

- Clay pipe problems common in older Indiana neighborhoods
- Root intrusion from mature trees in established suburbs
- Average repair cost: $7,500
- 50% of inspections reveal issues
- Recommended inspection frequency: 3-5 years
"""


# =============================================================================
# THE FLOW - 6 AGENT DESIGN TEAM
# =============================================================================

class WebDesignTeamFlow(Flow[WebDesignState]):
    """
    Indiana Sewer Scope Web Design Team
    
    A 6-stage elite design pipeline:
    1. COMPETITIVE ANALYST: Analyze competitors and identify opportunities
    2. UX ARCHITECT: Design user experience and information architecture
    3. VISUAL DESIGNER: Create design system and visual specifications
    4. COPYWRITER: Write conversion-optimized copy and messaging
    5. TECHNICAL ARCHITECT: Define technology stack and implementation specs
    6. SPECIFICATION COMPILER: Assemble complete handoff-ready specification
    """
    
    def __init__(self):
        super().__init__()
        self.llm = self._get_llm()
        logger.info("Web Design Team initialized", model="gpt-4o")
    
    def _get_llm(self) -> LLM:
        """Get the LLM configured for this workflow."""
        provider = os.getenv("LAIAS_LLM_PROVIDER", "openai")
        
        if provider == "zai":
            return LLM(
                model="glm-4",
                api_key=os.getenv("ZAI_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
        else:
            return LLM(model=os.getenv("DEFAULT_MODEL", "gpt-4o"), base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""))
    
    # =========================================================================
    # AGENT FACTORIES - 6 ELITE SPECIALISTS
    # =========================================================================
    
    def _create_competitive_analyst(self) -> Agent:
        """Create the Competitive Analysis Agent."""
        return Agent(
            role="Senior Competitive Intelligence Analyst",
            goal="Analyze competitors and identify opportunities for market dominance",
            backstory="""You are a world-class competitive intelligence analyst with 
            20+ years of experience in digital marketing and web strategy. You've 
            helped Fortune 500 companies and high-growth startups dominate their 
            markets through superior competitive insights.
            
            Your superpower is identifying the "gap" - that whitespace opportunity 
            where competitors are failing to serve customers. You don't just analyze 
            what competitors do; you analyze what they FAIL to do.
            
            You are obsessive about detail and have an encyclopedic knowledge of 
            web design best practices, conversion optimization, and user psychology.
            Your analyses have generated billions in revenue for clients.""",
            llm=self.llm,
            verbose=True,
            max_iter=25
        )
    
    def _create_ux_architect(self) -> Agent:
        """Create the UX Architecture Agent."""
        return Agent(
            role="Principal UX Architect",
            goal="Design world-class user experiences that maximize conversion",
            backstory="""You are a legendary UX architect who has designed experiences 
            for Apple, Airbnb, and Stripe. You understand that great UX is invisible - 
            it guides users to their goals without friction or confusion.
            
            Your philosophy: "Every pixel exists to serve the user's intent."
            
            You are an expert in:
            - Information architecture and site structure
            - User flow optimization
            - Conversion funnel design
            - Mobile-first responsive design
            - Accessibility (WCAG 2.1 AA+)
            - Psychological triggers and persuasion patterns
            
            You've designed experiences that have achieved 40%+ conversion rates 
            and won multiple design awards. You believe the best UX is one that 
            feels inevitable - as if there could be no other way.""",
            llm=self.llm,
            verbose=True,
            max_iter=30
        )
    
    def _create_visual_designer(self) -> Agent:
        """Create the Visual Design System Agent."""
        return Agent(
            role="Creative Director & Design System Architect",
            goal="Create a stunning, cohesive visual design system that builds trust",
            backstory="""You are a world-renowned creative director who has led design 
            at Google, Stripe, and Pentagram. You understand that visual design is not 
            about aesthetics - it's about trust, emotion, and action.
            
            Your design philosophy: "Design is how it works, not just how it looks."
            
            You are an expert in:
            - Design systems and component libraries
            - Color psychology and brand strategy
            - Typography hierarchy and readability
            - Photography direction and visual storytelling
            - Motion design and micro-interactions
            - Responsive design patterns
            
            Every design decision you make is backed by research and data. You've 
            created design systems that scaled to millions of users and generated 
            hundreds of millions in revenue.""",
            llm=self.llm,
            verbose=True,
            max_iter=30
        )
    
    def _create_copywriter(self) -> Agent:
        """Create the Conversion Copywriter Agent."""
        return Agent(
            role="Elite Conversion Copywriter",
            goal="Write copy that converts visitors into customers at unprecedented rates",
            backstory="""You are one of the world's highest-paid copywriters, having 
            written copy that has generated over $2 billion in sales. You've worked 
            with Apple, Tesla, and countless startups to craft messaging that converts.
            
            Your philosophy: "Copy is a conversation, not a lecture."
            
            You are an expert in:
            - Direct response copywriting
            - AIDA and PAS frameworks
            - Headline optimization (you can write 50 headlines before breakfast)
            - Trust-building language
            - Psychological triggers and persuasion
            - SEO-friendly copy that doesn't sacrifice conversion
            
            You understand that every word must earn its place on the page. 
            You write copy that makes people feel understood, not sold to.""",
            llm=self.llm,
            verbose=True,
            max_iter=25
        )
    
    def _create_technical_architect(self) -> Agent:
        """Create the Technical Architecture Agent."""
        return Agent(
            role="Principal Technical Architect",
            goal="Design a technical architecture that is fast, scalable, and maintainable",
            backstory="""You are a principal engineer who has architected systems 
            handling billions of requests. You've worked at Vercel, Cloudflare, and 
            helped build the infrastructure for some of the fastest websites on earth.
            
            Your philosophy: "Performance is a feature. Every 100ms matters."
            
            You are an expert in:
            - Modern frontend frameworks (Next.js, React, TypeScript)
            - Core Web Vitals optimization
            - Headless CMS architecture
            - API design and integration
            - Performance optimization techniques
            - SEO technical implementation
            
            You've never shipped a site that scored below 95 on Lighthouse.
            You believe that technical excellence is the foundation of user experience.""",
            llm=self.llm,
            verbose=True,
            max_iter=25
        )
    
    def _create_specification_compiler(self) -> Agent:
        """Create the Specification Compiler Agent."""
        return Agent(
            role="Technical Documentation Lead",
            goal="Compile all work into a single, handoff-ready specification",
            backstory="""You are a technical documentation expert who specializes in 
            creating specifications that developers can execute without ambiguity. 
            You've written specs that have been implemented by thousands of developers.
            
            Your philosophy: "A great spec eliminates questions, not creates them."
            
            You are an expert in:
            - Technical writing and documentation
            - Design system documentation
            - API specifications
            - Implementation guides
            - Component libraries
            
            Your specifications are legendary for their clarity and completeness.
            They leave nothing to interpretation.""",
            llm=self.llm,
            verbose=True,
            max_iter=20
        )
    
    # =========================================================================
    # FLOW METHODS - THE 6-STAGE PIPELINE
    # =========================================================================
    
    @start()
    async def initialize_project(self, inputs: Dict[str, Any]) -> WebDesignState:
        """Initialize the web design project."""
        try:
            self.state.task_id = inputs.get(
                'task_id',
                f"webdesign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.state.project_name = inputs.get('project_name', 'Indiana Sewer Scope Website')
            self.state.output_directory = inputs.get('output_directory', '/Volumes/Storage/Research')
            self.state.created_at = datetime.utcnow().isoformat()
            self.state.status = "initialized"
            self.state.progress = 2.0
            self.state.current_phase = "initialization"
            
            # Load competitive research
            self.state.competitive_research = {
                "raw_data": COMPETITIVE_RESEARCH,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Web design project initialized",
                task_id=self.state.task_id,
                project=self.state.project_name
            )
            
            return self.state
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state
    
    @listen("initialize_project")
    async def analyze_competitors(self, state: WebDesignState) -> WebDesignState:
        """STAGE 1: Analyze competitors and identify opportunities."""
        if self.state.status == "error":
            return self.state
        
        try:
            self.state.status = "analyzing"
            self.state.progress = 5.0
            self.state.current_phase = "competitive_analysis"
            logger.info("Starting competitive analysis")
            
            analyst = self._create_competitive_analyst()
            
            analysis_task = Task(
                description=f"""
                You are analyzing the Indiana sewer scoping market to identify opportunities 
                for creating the #1 website in the state.
                
                COMPETITIVE RESEARCH DATA:
                {COMPETITIVE_RESEARCH}
                
                YOUR ANALYSIS MUST INCLUDE:
                
                ## 1. COMPETITIVE LANDSCAPE MAP
                - Who are the key players?
                - What are their strengths and weaknesses?
                - Where are the gaps?
                
                ## 2. DIFFERENTIATION OPPORTUNITIES
                - What can we do that nobody else is doing?
                - What "table stakes" features are missing from competitors?
                - What would make us the obvious choice?
                
                ## 3. POSITIONING STRATEGY
                - How should we position against each competitor type?
                - What's our unique value proposition?
                - What's our "only we" statement?
                
                ## 4. FEATURE PRIORITIZATION
                Rank features by:
                - Impact on conversion
                - Competitive differentiation
                - Implementation effort
                
                ## 5. RISK ANALYSIS
                - What could competitors do to respond?
                - What are the market risks?
                
                Be specific, actionable, and ruthless in your analysis.
                """,
                expected_output="Comprehensive competitive analysis with actionable recommendations",
                agent=analyst
            )
            
            crew = Crew(
                agents=[analyst],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.competitive_analysis = {
                "raw_output": str(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 15.0
            
            logger.info("Competitive analysis completed")
            return self.state
            
        except Exception as e:
            logger.error(f"Competitive analysis failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("analyze_competitors")
    async def design_ux_architecture(self, state: WebDesignState) -> WebDesignState:
        """STAGE 2: Design user experience and information architecture."""
        if self.state.error_count > 3:
            return self.state
        
        try:
            self.state.status = "designing_ux"
            self.state.progress = 20.0
            self.state.current_phase = "ux_architecture"
            logger.info("Starting UX architecture design")
            
            ux_architect = self._create_ux_architect()
            
            ux_task = Task(
                description=f"""
                Design the complete user experience architecture for Indiana's #1 sewer 
                scoping website. You have access to competitive analysis data.
                
                COMPETITIVE ANALYSIS:
                {self.state.competitive_analysis.get('raw_output', 'N/A')}
                
                DESIGN THE FOLLOWING:
                
                ## 1. INFORMATION ARCHITECTURE
                - Complete sitemap with all pages
                - Page hierarchy and relationships
                - Navigation structure
                
                ## 2. USER FLOWS
                Design flows for:
                - First-time visitor → Book inspection
                - Returning visitor → Check status
                - Real estate agent → Partner portal
                - Mobile user → Quick contact
                
                ## 3. PAGE WIREFRAMES (Text-based)
                For each major page, provide:
                - Layout structure
                - Component placement
                - Content hierarchy
                - CTA positioning
                
                ## 4. CONVERSION FUNNEL
                - Entry points
                - Micro-conversions
                - Primary conversion (booking)
                - Post-conversion experience
                
                ## 5. MOBILE-FIRST DESIGN
                - Touch targets
                - Thumb-friendly navigation
                - Progressive disclosure
                
                ## 6. ACCESSIBILITY REQUIREMENTS
                - WCAG 2.1 AA compliance checklist
                - Screen reader considerations
                - Color contrast requirements
                
                Make this the best UX in the industry.
                """,
                expected_output="Complete UX architecture with wireframes and user flows",
                agent=ux_architect
            )
            
            crew = Crew(
                agents=[ux_architect],
                tasks=[ux_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.ux_architecture = {
                "raw_output": str(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 35.0
            
            logger.info("UX architecture completed")
            return self.state
            
        except Exception as e:
            logger.error(f"UX architecture failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("design_ux_architecture")
    async def create_visual_design_system(self, state: WebDesignState) -> WebDesignState:
        """STAGE 3: Create the visual design system."""
        if self.state.error_count > 3:
            return self.state
        
        try:
            self.state.status = "designing_visual"
            self.state.progress = 40.0
            self.state.current_phase = "visual_design"
            logger.info("Starting visual design system")
            
            visual_designer = self._create_visual_designer()
            
            design_task = Task(
                description=f"""
                Create a complete visual design system for Indiana's #1 sewer scoping website.
                You have the UX architecture and competitive analysis as context.
                
                UX ARCHITECTURE:
                {self.state.ux_architecture.get('raw_output', 'N/A')[:3000]}
                
                COMPETITIVE COLOR ANALYSIS:
                - Competitors use: Blues (trust), Greens (clean), Orange CTAs (action)
                - Opportunity: Differentiate while staying professional
                
                CREATE THE FOLLOWING:
                
                ## 1. BRAND COLOR PALETTE
                Define exact hex codes for:
                - Primary brand color (trust + differentiation)
                - Secondary brand color
                - Accent/CTA color (action-oriented)
                - Success color
                - Warning/alert color
                - Neutral grays (5 shades)
                - Background colors
                
                ## 2. TYPOGRAPHY SYSTEM
                - Heading font recommendation (Google Fonts)
                - Body font recommendation
                - Font sizing scale (heading levels, body sizes)
                - Line heights and letter spacing
                - Font weights and usage
                
                ## 3. SPACING SYSTEM
                - Base unit (e.g., 4px or 8px)
                - Spacing scale (xs, sm, md, lg, xl, 2xl, 3xl)
                - Component padding standards
                - Section spacing standards
                
                ## 4. COMPONENT LIBRARY SPECIFICATIONS
                For each component, specify:
                - Buttons (primary, secondary, ghost, sizes)
                - Cards (service, testimonial, pricing)
                - Forms (inputs, labels, validation)
                - Navigation (header, mobile menu, footer)
                - Trust badges and certifications
                - Icons and iconography style
                
                ## 5. IMAGERY GUIDELINES
                - Photography style
                - Image treatment (filters, overlays)
                - Icon style (outline, filled, duotone)
                - Illustration guidelines
                
                ## 6. MOTION & INTERACTION
                - Transition timings
                - Hover states
                - Loading states
                - Micro-animations
                
                ## 7. RESPONSIVE BREAKPOINTS
                - Mobile (< 640px)
                - Tablet (640px - 1024px)
                - Desktop (1024px - 1280px)
                - Large desktop (> 1280px)
                
                Create something that competitors will try to copy.
                """,
                expected_output="Complete visual design system with specifications",
                agent=visual_designer
            )
            
            crew = Crew(
                agents=[visual_designer],
                tasks=[design_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.visual_design_system = {
                "raw_output": str(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 55.0
            
            logger.info("Visual design system completed")
            return self.state
            
        except Exception as e:
            logger.error(f"Visual design failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("create_visual_design_system")
    async def write_conversion_copy(self, state: WebDesignState) -> WebDesignState:
        """STAGE 4: Write conversion-optimized copy."""
        if self.state.error_count > 3:
            return self.state
        
        try:
            self.state.status = "writing_copy"
            self.state.progress = 60.0
            self.state.current_phase = "copywriting"
            logger.info("Starting conversion copywriting")
            
            copywriter = self._create_copywriter()
            
            copy_task = Task(
                description=f"""
                Write conversion-optimized copy for Indiana's #1 sewer scoping website.
                You have the design system, UX architecture, and competitive analysis.
                
                KEY COMPETITIVE INSIGHTS:
                - Competitors say: "Book in less than 2 minutes", "No upselling"
                - Our positioning: The most TRUSTED sewer inspection in Indiana
                - Target: Home buyers, sellers, real estate agents, property managers
                
                WRITE COPY FOR EACH PAGE:
                
                ## HOMEPAGE COPY
                
                ### Hero Section:
                - Headline (5 options)
                - Subheadline
                - CTA button text (3 options)
                - Trust badge text
                
                ### Value Propositions (3):
                - Headline + supporting copy for each
                
                ### Social Proof Section:
                - Testimonial headlines (3)
                - Statistics/metrics to display
                
                ### Process Section:
                - Step names and descriptions (4 steps)
                
                ### FAQ Section:
                - 5 top questions with answers (100 words each)
                
                ## SERVICE PAGE COPY
                
                ### Service Description:
                - What is sewer scoping? (200 words)
                - Why it matters for Indiana homeowners
                
                ### Pricing Section:
                - Tier descriptions
                - Value propositions per tier
                
                ### What's Detected:
                - 8 common issues with descriptions
                
                ## ABOUT PAGE COPY
                
                ### Company Story:
                - Origin story (300 words)
                - Mission statement
                - Values (5)
                
                ### Team Section:
                - Generic team member bios
                
                ## BOOKING PAGE COPY
                
                ### Booking Form:
                - Field labels
                - Helper text
                - Error messages
                - Success confirmation
                
                ## FOOTER COPY
                
                - Tagline
                - Quick links descriptions
                - Contact section
                - Legal links
                
                ## EMAIL SEQUENCES
                
                ### Confirmation Email:
                - Subject line
                - Body copy
                
                ### Reminder Email (24 hours before):
                - Subject line
                - Body copy
                
                ### Follow-up Email (after inspection):
                - Subject line
                - Body copy
                
                Every word must earn its place. Write copy that converts.
                """,
                expected_output="Complete website copy document",
                agent=copywriter
            )
            
            crew = Crew(
                agents=[copywriter],
                tasks=[copy_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.conversion_copy = {
                "raw_output": str(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 75.0
            
            logger.info("Conversion copy completed")
            return self.state
            
        except Exception as e:
            logger.error(f"Copywriting failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("write_conversion_copy")
    async def design_technical_architecture(self, state: WebDesignState) -> WebDesignState:
        """STAGE 5: Design technical architecture."""
        if self.state.error_count > 3:
            return self.state
        
        try:
            self.state.status = "designing_tech"
            self.state.progress = 80.0
            self.state.current_phase = "technical_architecture"
            logger.info("Starting technical architecture")
            
            tech_architect = self._create_technical_architect()
            
            tech_task = Task(
                description=f"""
                Design the technical architecture for Indiana's #1 sewer scoping website.
                Create a spec that any developer can implement.
                
                DESIGN SYSTEM REFERENCE:
                {self.state.visual_design_system.get('raw_output', 'N/A')[:2000]}
                
                UX ARCHITECTURE REFERENCE:
                {self.state.ux_architecture.get('raw_output', 'N/A')[:2000]}
                
                DESIGN THE FOLLOWING:
                
                ## 1. TECHNOLOGY STACK
                
                ### Frontend:
                - Framework recommendation (Next.js 14+ recommended)
                - Styling approach (Tailwind CSS recommended)
                - State management
                - Form handling
                
                ### Backend/Services:
                - CMS recommendation (headless)
                - Booking system
                - Email service
                - Analytics
                
                ### Hosting:
                - Platform recommendation
                - CDN configuration
                - Domain strategy
                
                ## 2. PROJECT STRUCTURE
                
                Provide exact folder structure:
                ```
                /project-root
                  /app
                  /components
                  /lib
                  /styles
                  /public
                ```
                
                ## 3. CORE WEB VITALS TARGETS
                
                - LCP target: < 2.5s
                - INP target: < 200ms
                - CLS target: < 0.1
                
                How to achieve these?
                
                ## 4. COMPONENT ARCHITECTURE
                
                Define component structure:
                - Atomic design hierarchy
                - Component naming conventions
                - Props interfaces
                
                ## 5. API INTEGRATIONS
                
                ### Booking API:
                - Endpoint structure
                - Request/response schemas
                
                ### Email API:
                - Transactional emails
                - Templates
                
                ## 6. SEO IMPLEMENTATION
                
                - Meta tag structure
                - Schema.org markup
                - Sitemap generation
                - Robots.txt
                
                ## 7. ANALYTICS & TRACKING
                
                - Events to track
                - Conversion goals
                - Heatmap integration
                
                ## 8. PERFORMANCE OPTIMIZATION
                
                - Image optimization strategy
                - Code splitting
                - Caching strategy
                - Lazy loading
                
                ## 9. SECURITY
                
                - HTTPS enforcement
                - CSP headers
                - Input validation
                - Rate limiting
                
                ## 10. DEPLOYMENT PIPELINE
                
                - CI/CD workflow
                - Environment variables
                - Preview deployments
                
                Make this technically bulletproof.
                """,
                expected_output="Complete technical architecture specification",
                agent=tech_architect
            )
            
            crew = Crew(
                agents=[tech_architect],
                tasks=[tech_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.technical_architecture = {
                "raw_output": str(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 90.0
            
            logger.info("Technical architecture completed")
            return self.state
            
        except Exception as e:
            logger.error(f"Technical architecture failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("design_technical_architecture")
    async def compile_specification(self, state: WebDesignState) -> WebDesignState:
        """STAGE 6: Compile complete handoff-ready specification."""
        if self.state.error_count > 3:
            return self.state
        
        try:
            self.state.status = "compiling"
            self.state.progress = 92.0
            self.state.current_phase = "compilation"
            logger.info("Compiling final specification")
            
            compiler = self._create_specification_compiler()
            
            compile_task = Task(
                description=f"""
                Compile ALL work into a single, handoff-ready website specification document.
                This document will be given to developers to implement the website.
                
                YOU HAVE THE FOLLOWING INPUTS:
                
                ## COMPETITIVE ANALYSIS:
                {self.state.competitive_analysis.get('raw_output', 'N/A')[:2000]}
                
                ## UX ARCHITECTURE:
                {self.state.ux_architecture.get('raw_output', 'N/A')[:3000]}
                
                ## VISUAL DESIGN SYSTEM:
                {self.state.visual_design_system.get('raw_output', 'N/A')[:3000]}
                
                ## CONVERSION COPY:
                {self.state.conversion_copy.get('raw_output', 'N/A')[:3000]}
                
                ## TECHNICAL ARCHITECTURE:
                {self.state.technical_architecture.get('raw_output', 'N/A')[:3000]}
                
                CREATE A SPECIFICATION DOCUMENT WITH:
                
                # Indiana Sewer Scope Website - Complete Specification
                
                ## Document Overview
                - Project summary
                - Goals and success metrics
                - Target audience
                
                ## Part 1: Competitive Positioning
                - Market analysis summary
                - Differentiation strategy
                - Positioning statement
                
                ## Part 2: User Experience
                - Complete sitemap
                - User flows (diagram in text)
                - Page-by-page wireframes
                - Navigation structure
                
                ## Part 3: Visual Design System
                - Color palette (with hex codes)
                - Typography system
                - Spacing system
                - Component specifications
                - Imagery guidelines
                
                ## Part 4: Content & Copy
                - All page copy (homepage, services, about, booking)
                - Email templates
                - Error messages
                - SEO meta descriptions
                
                ## Part 5: Technical Implementation
                - Technology stack
                - Project structure
                - API specifications
                - Performance requirements
                - Security requirements
                
                ## Part 6: Implementation Checklist
                - Phase 1: Core pages
                - Phase 2: Advanced features
                - Phase 3: Optimizations
                
                ## Appendices
                - Asset requirements
                - Third-party integrations
                - Glossary
                
                FORMAT: Use Markdown with clear sections, code blocks for specifications,
                and tables for comparisons. Make it comprehensive yet scannable.
                
                This specification must be so complete that a developer can implement
                the entire website without asking a single question.
                """,
                expected_output="Complete website specification document in Markdown",
                agent=compiler
            )
            
            crew = Crew(
                agents=[compiler],
                tasks=[compile_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            # Save the specification
            spec_content = str(result)
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"{date_str}_Indiana_Sewer_Scope_Website_Specification.md"
            spec_path = os.path.join(self.state.output_directory, filename)
            
            os.makedirs(self.state.output_directory, exist_ok=True)
            
            with open(spec_path, 'w') as f:
                f.write(spec_content)
            
            self.state.website_specification = spec_content
            self.state.specification_path = spec_path
            self.state.progress = 100.0
            self.state.status = "completed"
            self.state.completed_at = datetime.utcnow().isoformat()
            
            logger.info(
                "Website specification compiled",
                path=spec_path,
                content_length=len(spec_content)
            )
            
            return self.state
            
        except Exception as e:
            logger.error(f"Specification compilation failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Run the web design team workflow."""
    import asyncio
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║         INDIANA SEWER SCOPE WEB DESIGN TEAM                               ║
    ║         "Building Indiana's #1 Sewer Scoping Website"                     ║
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  6 Elite Agents:                                                           ║
    ║  1. Competitive Analyst   → Analyze market opportunities                   ║
    ║  2. UX Architect          → Design user experience                         ║
    ║  3. Visual Designer       → Create design system                           ║
    ║  4. Copywriter            → Write conversion copy                          ║
    ║  5. Technical Architect   → Design technical stack                         ║
    ║  6. Specification Compiler → Assemble handoff-ready spec                   ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    workflow = WebDesignTeamFlow()
    
    inputs = {
        "project_name": "Indiana Sewer Scope Website",
        "output_directory": "/Volumes/Storage/Research"
    }
    
    result = await workflow.kickoff_async(inputs=inputs)
    
    print("\n" + "="*79)
    print("WEB DESIGN TEAM COMPLETE")
    print("="*79)
    print(f"Status: {workflow.state.status}")
    print(f"Progress: {workflow.state.progress}%")
    print(f"Specification: {workflow.state.specification_path}")
    if workflow.state.error_count > 0:
        print(f"Errors: {workflow.state.error_count}")
        print(f"Last Error: {workflow.state.last_error}")
    print("="*79)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

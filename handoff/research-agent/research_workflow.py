"""
================================================================================
            PORTABLE RESEARCH WORKFLOW
            "From Question to Actionable Intelligence"
================================================================================

A 4-agent research pipeline that takes a topic, researches it deeply,
analyzes it for your business context, documents the findings, and
optionally generates action items.

FLOW:
    Trigger (webhook/manual) → Research → Analyze → Document → Build

This is a portable version that can be configured for any LLM provider.

Author: Research Agent Template
Version: 1.0.0
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
import yaml

# =============================================================================
# LOGGING
# =============================================================================

logger = structlog.get_logger()


# =============================================================================
# CONFIGURATION
# =============================================================================

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml or environment variables."""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    
    # Default config
    config = {
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "openai"),
            "model": os.getenv("LLM_MODEL", "gpt-4o"),
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": os.getenv("LLM_BASE_URL", None),
        },
        "output_directory": os.getenv("OUTPUT_DIR", "./research_output"),
        "business_context": {
            "name": "Your Business",
            "description": "Your business description here",
            "focus_areas": ["general research"],
        },
        "agents": {
            "researcher": {"max_iter": 20},
            "analyst": {"max_iter": 15},
            "documenter": {"max_iter": 10},
            "builder": {"max_iter": 25},
        },
    }
    
    # Load from YAML if exists
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                config = {**config, **yaml_config}
    
    return config


# =============================================================================
# STATE CLASS
# =============================================================================

class ResearchWorkflowState(BaseModel):
    """State for the Research Workflow."""
    
    # Execution Identity
    task_id: str = Field(default="", description="Unique task identifier")
    research_topic: str = Field(default="", description="Topic to research")
    
    # Status Tracking
    status: str = Field(default="pending")
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Error Handling
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)
    
    # Agent Outputs
    research_findings: Dict[str, Any] = Field(default_factory=dict)
    analysis: Dict[str, Any] = Field(default_factory=dict)
    documentation_path: Optional[str] = Field(default=None)
    generated_actions: Optional[str] = Field(default=None)
    
    # Configuration
    output_directory: str = Field(default="./research_output")
    max_retries: int = Field(default=3)
    
    # Metadata
    created_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


# =============================================================================
# THE FLOW
# =============================================================================

class ResearchWorkflow(Flow[ResearchWorkflowState]):
    """
    Portable Research Workflow
    
    A 4-stage pipeline:
    1. RESEARCH: Deep research on the topic
    2. ANALYZE: Apply findings to your business context
    3. DOCUMENT: Create structured documentation
    4. BUILD: Generate action items if needed
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or load_config()
        self.llm = self._get_llm()
        logger.info("Research Workflow initialized", config=self.config)
    
    def _get_llm(self) -> LLM:
        """Get the LLM configured for this workflow."""
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider", "openai")
        model = llm_config.get("model", "gpt-4o")
        api_key = llm_config.get("api_key", "")
        base_url = llm_config.get("base_url")
        
        # Provider-specific configurations
        if provider == "anthropic":
            return LLM(
                model=f"anthropic/{model}",
                api_key=api_key
            )
        elif provider == "openai":
            if base_url:
                return LLM(
                    model=model,
                    api_key=api_key,
                    base_url=base_url
                )
            return LLM(model=model, api_key=api_key)
        elif provider == "ollama":
            return LLM(
                model=f"ollama/{model}",
                base_url=base_url or "http://localhost:11434"
            )
        elif provider == "groq":
            return LLM(
                model=f"groq/{model}",
                api_key=api_key
            )
        else:
            # Generic OpenAI-compatible
            return LLM(
                model=model,
                api_key=api_key,
                base_url=base_url
            )
    
    # =========================================================================
    # AGENT FACTORIES
    # =========================================================================
    
    def _create_researcher(self) -> Agent:
        """Create the Research Agent."""
        return Agent(
            role="Senior Research Analyst",
            goal="Conduct comprehensive research and gather actionable intelligence",
            backstory="""You are an expert researcher with 15+ years of experience 
            in technology and business research. You excel at finding relevant 
            information, verifying sources, and synthesizing findings into 
            structured, actionable insights. You are thorough but efficient.""",
            llm=self.llm,
            verbose=True,
            max_iter=self.config.get("agents", {}).get("researcher", {}).get("max_iter", 20)
        )
    
    def _create_analyst(self) -> Agent:
        """Create the Business Analyst Agent."""
        business = self.config.get("business_context", {})
        business_name = business.get("name", "Your Business")
        business_desc = business.get("description", "Your business description")
        focus_areas = business.get("focus_areas", ["general research"])
        
        return Agent(
            role="Strategic Business Analyst",
            goal="Analyze research findings and identify opportunities",
            backstory=f"""You are a strategic analyst specializing in business 
            and technology analysis. You understand {business_name}'s context:
            - Business: {business_desc}
            - Focus Areas: {', '.join(focus_areas)}
            
            You identify how research findings apply to this specific context
            and prioritize opportunities by impact and feasibility.""",
            llm=self.llm,
            verbose=True,
            max_iter=self.config.get("agents", {}).get("analyst", {}).get("max_iter", 15)
        )
    
    def _create_documenter(self) -> Agent:
        """Create the Documenter Agent."""
        return Agent(
            role="Technical Documentation Specialist",
            goal="Create clear, well-organized documentation following best practices",
            backstory="""You are a technical writer who creates documentation 
            that is both comprehensive and accessible. You follow document 
            management best practices:
            - YYYY-MM-DD_[Topic].md naming convention
            - Structured sections with clear hierarchy
            - Executive summaries for quick scanning
            - Actionable recommendations
            - Proper categorization and tagging""",
            llm=self.llm,
            verbose=True,
            max_iter=self.config.get("agents", {}).get("documenter", {}).get("max_iter", 10)
        )
    
    def _create_builder(self) -> Agent:
        """Create the Action Builder Agent."""
        return Agent(
            role="Action Item Architect",
            goal="Generate actionable next steps based on research findings",
            backstory="""You are an expert in creating actionable plans from 
            research findings. You generate practical, prioritized action items:
            - Immediate actions (next 7 days)
            - Short-term (next 30 days)
            - Long-term considerations
            - Resource requirements
            - Success metrics
            
            You only generate actions when they are genuinely needed and useful.""",
            llm=self.llm,
            verbose=True,
            max_iter=self.config.get("agents", {}).get("builder", {}).get("max_iter", 25)
        )
    
    # =========================================================================
    # FLOW METHODS
    # =========================================================================
    
    @start()
    async def initialize_workflow(self, inputs: Dict[str, Any]) -> ResearchWorkflowState:
        """Initialize the research workflow."""
        try:
            self.state.task_id = inputs.get(
                'task_id',
                f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.state.research_topic = inputs.get('topic', inputs.get('research_topic', ''))
            self.state.output_directory = inputs.get(
                'output_directory',
                self.config.get('output_directory', './research_output')
            )
            self.state.created_at = datetime.utcnow().isoformat()
            self.state.status = "initialized"
            self.state.progress = 5.0
            
            logger.info(
                "Research workflow initialized",
                task_id=self.state.task_id,
                topic=self.state.research_topic
            )
            
            return self.state
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state
    
    @listen("initialize_workflow")
    async def conduct_research(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 1: Conduct deep research on the topic."""
        if self.state.status == "error":
            return self.state
        
        try:
            self.state.status = "researching"
            self.state.progress = 10.0
            logger.info("Starting research", topic=self.state.research_topic)
            
            researcher = self._create_researcher()
            
            research_task = Task(
                description=f"""
                Conduct comprehensive research on: {self.state.research_topic}
                
                Your research should:
                1. Define the topic and its significance
                2. Gather information from multiple perspectives
                3. Identify key players, technologies, or concepts
                4. Note recent developments and trends
                5. Find data, statistics, or evidence
                6. Identify knowledge gaps or uncertainties
                
                Output a structured research summary with:
                - Overview
                - Key Findings (bullet points with sources)
                - Trends and Patterns
                - Open Questions
                - Source List
                """,
                expected_output="Structured research summary with citations",
                agent=researcher
            )
            
            crew = Crew(
                agents=[researcher],
                tasks=[research_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.research_findings = {
                "raw_output": str(result),
                "topic": self.state.research_topic,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 35.0
            
            logger.info("Research completed", task_id=self.state.task_id)
            return self.state
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("conduct_research")
    async def analyze_findings(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 2: Analyze findings for business context."""
        if self.state.error_count > self.state.max_retries:
            return self.state
        
        try:
            self.state.status = "analyzing"
            self.state.progress = 40.0
            logger.info("Starting analysis")
            
            analyst = self._create_analyst()
            business = self.config.get("business_context", {})
            
            analysis_task = Task(
                description=f"""
                Analyze the following research findings for {business.get('name', 'our business')}:
                
                RESEARCH FINDINGS:
                {self.state.research_findings.get('raw_output', 'No findings available')}
                
                YOUR ANALYSIS SHOULD ADDRESS:
                1. RELEVANCE: How does this apply to our business?
                   - {business.get('description', 'Our business focus')}
                   - Focus areas: {', '.join(business.get('focus_areas', ['general']))}
                
                2. OPPORTUNITIES: What opportunities does this create?
                   - New features or products
                   - Market positioning
                   - Competitive advantages
                
                3. THREATS: What risks or challenges does this present?
                
                4. ACTIONS: What should we do about this?
                   - Immediate actions (next 7 days)
                   - Short-term (next 30 days)
                   - Long-term considerations
                
                5. PRIORITY: Rank opportunities by impact and feasibility
                
                Output a structured analysis with clear recommendations.
                """,
                expected_output="Strategic analysis with prioritized recommendations",
                agent=analyst
            )
            
            crew = Crew(
                agents=[analyst],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.analysis = {
                "raw_output": str(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.state.progress = 65.0
            
            logger.info("Analysis completed", task_id=self.state.task_id)
            return self.state
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen("analyze_findings")
    async def create_documentation(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 3: Create structured documentation."""
        if self.state.error_count > self.state.max_retries:
            return self.state
        
        try:
            self.state.status = "documenting"
            self.state.progress = 70.0
            logger.info("Creating documentation")
            
            documenter = self._create_documenter()
            
            # Generate document filename
            date_str = datetime.now().strftime('%Y-%m-%d')
            safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in self.state.research_topic)
            safe_topic = safe_topic[:50].strip().replace(' ', '_')
            filename = f"{date_str}_{safe_topic}.md"
            
            doc_task = Task(
                description=f"""
                Create a comprehensive research document following best practices.
                
                RESEARCH FINDINGS:
                {self.state.research_findings.get('raw_output', 'N/A')}
                
                ANALYSIS:
                {self.state.analysis.get('raw_output', 'N/A')}
                
                DOCUMENT STRUCTURE:
                
                # {self.state.research_topic}
                
                **Date:** {date_str}
                **Document Type:** Research Analysis
                **Status:** Complete
                
                ---
                
                ## Executive Summary
                [2-3 paragraph overview for quick reading]
                
                ## Key Findings
                [Bulleted list of most important discoveries]
                
                ## Relevance
                [How this applies to our business]
                
                ## Opportunities
                [Ranked list of actionable opportunities]
                
                ## Recommendations
                [Specific next steps with priority levels]
                
                ## Open Questions
                [What we still don't know]
                
                ## Sources
                [List of references]
                
                ---
                
                *Generated by Research Workflow*
                
                OUTPUT THE COMPLETE MARKDOWN DOCUMENT.
                """,
                expected_output="Complete markdown document",
                agent=documenter
            )
            
            crew = Crew(
                agents=[documenter],
                tasks=[doc_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            # Save the document
            doc_content = str(result)
            doc_path = os.path.join(self.state.output_directory, filename)
            
            # Ensure directory exists
            os.makedirs(self.state.output_directory, exist_ok=True)
            
            with open(doc_path, 'w') as f:
                f.write(doc_content)
            
            self.state.documentation_path = doc_path
            self.state.progress = 85.0
            
            logger.info("Documentation created", path=doc_path)
            return self.state
            
        except Exception as e:
            logger.error(f"Documentation failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @router(create_documentation)
    def determine_action_need(self) -> str:
        """Determine if action items need to be generated."""
        # Check if analysis indicates actions are needed
        analysis = self.state.analysis.get('raw_output', '')
        
        action_keywords = [
            'action required',
            'next steps',
            'implement this',
            'create a plan',
            'should be done',
            'recommended actions',
            'to-do'
        ]
        
        if any(kw in analysis.lower() for kw in action_keywords):
            logger.info("Action item generation triggered based on analysis")
            return "build_actions"
        
        logger.info("No action item generation needed")
        return "finalize"
    
    @listen("build_actions")
    async def build_actions(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 4: Build action items if needed."""
        try:
            self.state.status = "building"
            self.state.progress = 90.0
            logger.info("Building action items")
            
            builder = self._create_builder()
            
            build_task = Task(
                description=f"""
                Based on the research and analysis, generate a prioritized action plan.
                
                RESEARCH TOPIC: {self.state.research_topic}
                
                ANALYSIS:
                {self.state.analysis.get('raw_output', 'N/A')}
                
                Generate a structured action plan that includes:
                1. IMMEDIATE ACTIONS (Next 7 Days)
                   - Specific tasks
                   - Owner/role responsible
                   - Success criteria
                
                2. SHORT-TERM ACTIONS (Next 30 Days)
                   - Projects or initiatives
                   - Resources needed
                   - Dependencies
                
                3. LONG-TERM CONSIDERATIONS
                   - Strategic implications
                   - Investment needs
                   - Timeline considerations
                
                4. METRICS FOR SUCCESS
                   - KPIs to track
                   - How to measure impact
                
                Output the complete action plan.
                """,
                expected_output="Complete action plan with priorities",
                agent=builder
            )
            
            crew = Crew(
                agents=[builder],
                tasks=[build_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.generated_actions = str(result)
            self.state.progress = 95.0
            
            logger.info("Action items built", task_id=self.state.task_id)
            return self.state
            
        except Exception as e:
            logger.error(f"Action building failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen(or_("finalize", "build_actions"))
    async def finalize(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Finalize the workflow and return results."""
        try:
            self.state.status = "completed"
            self.state.progress = 100.0
            self.state.completed_at = datetime.utcnow().isoformat()
            
            # Store results in a summary
            summary = {
                "task_id": self.state.task_id,
                "topic": self.state.research_topic,
                "status": self.state.status,
                "documentation_path": self.state.documentation_path,
                "actions_generated": self.state.generated_actions is not None,
                "created_at": self.state.created_at,
                "completed_at": self.state.completed_at
            }
            
            # Save summary
            summary_path = os.path.join(
                self.state.output_directory, 
                f"{self.state.task_id}_summary.json"
            )
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info("Research workflow completed", **summary)
            
            return self.state
            
        except Exception as e:
            logger.error(f"Finalization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Run the research workflow."""
    import asyncio
    
    # Get topic from environment or user input
    topic = os.getenv("RESEARCH_TOPIC")
    if not topic:
        topic = input("Enter your research topic: ")
    
    workflow = ResearchWorkflow()
    
    inputs = {
        "topic": topic,
    }
    
    result = await workflow.kickoff_async(inputs=inputs)
    
    print("\n" + "="*60)
    print("RESEARCH WORKFLOW COMPLETE")
    print("="*60)
    print(f"Status: {workflow.state.status}")
    print(f"Progress: {workflow.state.progress}%")
    print(f"Documentation: {workflow.state.documentation_path}")
    if workflow.state.generated_actions:
        print(f"Actions Generated: Yes")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

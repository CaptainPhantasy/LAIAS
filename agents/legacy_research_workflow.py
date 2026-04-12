"""
================================================================================
            LEGACY AI RESEARCH WORKFLOW
            "From Question to Actionable Intelligence"
================================================================================

A 4-agent research pipeline that takes a topic, researches it deeply,
analyzes it for Legacy AI's context, documents the findings, and
optionally generates new workflows.

FLOW:
    Trigger (webhook/manual) → Research → Analyze → Document → Build

Author: Legacy AI
Date: February 2026
Version: 1.0
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
    legacy_analysis: Dict[str, Any] = Field(default_factory=dict)
    documentation_path: Optional[str] = Field(default=None)
    generated_workflow: Optional[str] = Field(default=None)
    
    # Configuration
    output_directory: str = Field(default="/Volumes/Storage/Research")
    max_retries: int = Field(default=3)
    
    # Metadata
    created_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


# =============================================================================
# THE FLOW
# =============================================================================

class LegacyResearchWorkflow(Flow[ResearchWorkflowState]):
    """
    Legacy AI Research Workflow
    
    A 4-stage pipeline:
    1. RESEARCH: Deep web research on the topic
    2. ANALYZE: Apply findings to Legacy AI context
    3. DOCUMENT: Create structured documentation
    4. BUILD: Generate workflows if needed
    """
    
    def __init__(self):
        super().__init__()
        self.llm = self._get_llm()
        logger.info("Legacy Research Workflow initialized")
    
    def _get_llm(self) -> LLM:
        """Get the LLM configured for this workflow."""
        # Try ZAI first, fall back to OpenAI
        provider = os.getenv("LAIAS_LLM_PROVIDER", "zai")
        model = os.getenv("LAIAS_LLM_MODEL", "glm-4")
        
        if provider == "zai":
            return LLM(
                model="glm-4",
                api_key=os.getenv("ZAI_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
        else:
            return LLM(model=model or "gpt-4o", base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""))
    
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
            max_iter=20
        )
    
    def _create_analyst(self) -> Agent:
        """Create the Legacy AI Analyst Agent."""
        return Agent(
            role="Legacy AI Strategy Analyst",
            goal="Analyze research findings and identify opportunities for Legacy AI",
            backstory="""You are a strategic analyst specializing in AI tooling 
            and solo founder businesses. You understand Legacy AI's ecosystem:
            - FLOYD: AI coding assistant ecosystem
            - LAIAS: Agent factory platform
            - SUPERCACHE: 3-tier memory system
            - Philosophy: BALLS (Borderless, Autonomous, Loud, Living, Subversive)
            - Founder: Douglas Talley, solo developer in Indiana
            
            You identify how research findings apply to this specific context
            and prioritize opportunities by impact and feasibility.""",
            llm=self.llm,
            verbose=True,
            max_iter=15
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
            max_iter=10
        )
    
    def _create_workflow_builder(self) -> Agent:
        """Create the Workflow Builder Agent."""
        return Agent(
            role="Agent Workflow Architect",
            goal="Generate CrewAI workflow code following the Godzilla pattern",
            backstory="""You are an expert in CrewAI and the Godzilla architectural 
            pattern. You generate production-ready agent code that includes:
            - Typed state management with Pydantic
            - Event-driven architecture with @start, @listen, @router decorators
            - Error handling with retry logic
            - Analytics and monitoring integration
            
            You only generate code when a new workflow is genuinely needed.""",
            llm=self.llm,
            verbose=True,
            max_iter=25
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
                '/Volumes/Storage/Research'
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
    async def analyze_for_legacy(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 2: Analyze findings for Legacy AI context."""
        if self.state.error_count > self.state.max_retries:
            return self.state
        
        try:
            self.state.status = "analyzing"
            self.state.progress = 40.0
            logger.info("Starting Legacy AI analysis")
            
            analyst = self._create_analyst()
            
            analysis_task = Task(
                description=f"""
                Analyze the following research findings for Legacy AI:
                
                RESEARCH FINDINGS:
                {self.state.research_findings.get('raw_output', 'No findings available')}
                
                YOUR ANALYSIS SHOULD ADDRESS:
                1. RELEVANCE: How does this apply to Legacy AI's business?
                   - FLOYD ecosystem (AI coding assistant)
                   - LAIAS platform (agent factory)
                   - Solo founder model
                
                2. OPPORTUNITIES: What opportunities does this create?
                   - New features or products
                   - Market positioning
                   - Competitive advantages
                
                3. THREATS: What risks or challenges does this present?
                
                4. ACTIONS: What should Legacy AI do about this?
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
            
            self.state.legacy_analysis = {
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
    
    @listen("analyze_for_legacy")
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
                
                LEGACY AI ANALYSIS:
                {self.state.legacy_analysis.get('raw_output', 'N/A')}
                
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
                
                ## Legacy AI Relevance
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
                
                *Generated by Legacy AI Research Workflow*
                
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
    def determine_build_need(self) -> str:
        """Determine if a new workflow needs to be built."""
        # Check if analysis indicates a workflow is needed
        analysis = self.state.legacy_analysis.get('raw_output', '')
        
        workflow_keywords = [
            'automate this',
            'create an agent',
            'build a workflow',
            'new agent needed',
            'should be automated',
            'workflow required'
        ]
        
        if any(kw in analysis.lower() for kw in workflow_keywords):
            logger.info("Workflow build triggered based on analysis")
            return "build_workflow"
        
        logger.info("No workflow build needed")
        return "finalize"
    
    @listen("build_workflow")
    async def build_workflow(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        """Stage 4: Build a new workflow if needed."""
        try:
            self.state.status = "building"
            self.state.progress = 90.0
            logger.info("Building new workflow")
            
            builder = self._create_workflow_builder()
            
            build_task = Task(
                description=f"""
                Based on the research and analysis, generate a CrewAI workflow 
                following the Godzilla pattern.
                
                RESEARCH TOPIC: {self.state.research_topic}
                
                ANALYSIS:
                {self.state.legacy_analysis.get('raw_output', 'N/A')}
                
                Generate a complete Python file that:
                1. Follows the Godzilla architectural pattern
                2. Uses typed state with Pydantic BaseModel
                3. Has event-driven flow with @start, @listen, @router decorators
                4. Includes error handling and retry logic
                5. Is production-ready
                
                Output the complete Python code.
                """,
                expected_output="Complete Python workflow code",
                agent=builder
            )
            
            crew = Crew(
                agents=[builder],
                tasks=[build_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = await crew.kickoff_async()
            
            self.state.generated_workflow = str(result)
            self.state.progress = 95.0
            
            logger.info("Workflow built", task_id=self.state.task_id)
            return self.state
            
        except Exception as e:
            logger.error(f"Workflow build failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state
    
    @listen(or_("finalize", "build_workflow"))
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
                "workflow_generated": self.state.generated_workflow is not None,
                "created_at": self.state.created_at,
                "completed_at": self.state.completed_at
            }
            
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
    
    # Get topic from environment or use default
    topic = os.getenv("RESEARCH_TOPIC", "Best practices for LinkedIn posting times for AI/tech founders")
    
    workflow = LegacyResearchWorkflow()
    
    inputs = {
        "topic": topic,
        "output_directory": "/Volumes/Storage/Research"
    }
    
    result = await workflow.kickoff_async(inputs=inputs)
    
    print("\n" + "="*60)
    print("RESEARCH WORKFLOW COMPLETE")
    print("="*60)
    print(f"Status: {workflow.state.status}")
    print(f"Progress: {workflow.state.progress}%")
    print(f"Documentation: {workflow.state.documentation_path}")
    if workflow.state.generated_workflow:
        print(f"Workflow Generated: Yes")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

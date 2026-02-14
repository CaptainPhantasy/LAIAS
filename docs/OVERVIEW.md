![](LAIAS/las.png)


# Goal:** Build a Dockerized application called “Legacy AI Agent Studio." This platform must allow me to:
1. **Describe an agent idea** in natural language (e.g., "Make a market research swarm").
2. **Have an LLM (You)** generate the python code for that flow, using the "Gold Standard" architecture I will provide as a reference style.
3. **Save, Edit, and Run** these generated agents in isolated Docker containers.
4. **Monitor** their execution via a dashboard.

⠀**Core Components to Build:**
**1\. The "Architect" Engine (FastAPI + DSPy/LangChain)**
* Create a "Generator Endpoint" (POST /api/generate-agent):
  * Input: User's natural language description.
  * Action: Uses an LLM to write a valid flow.py and agents.yaml file.
  * **CRITICAL CONSTRAINT:** The generated code **MUST** follow the architectural pattern of the "Godzilla" class I am providing (using Flow[AgentState], @start, @listen, and typed state), but adapted to the user's specific request (simple or complex).
* Create a "Manager Endpoint" (POST /api/deploy):
  * Takes the generated Python code and spins it up as a background worker (Celery) or a separate Docker service.

⠀**2. The Studio UI (Next.js 15 + React Flow)**
* **Chat-to-Agent Interface:** A chat window where I describe what I want.
* **Code Editor:** A Monaco Editor window to review/tweak the Python code the Architect generated before I click "Deploy".
* **Visual Graph:** Use React Flow to visualize the nodes/edges of the agent I just built.
* **Control Room:** A list of all my deployed agents with "Start", "Stop", and "Logs" buttons.

⠀**3. The "Godzilla" Template**
* Use the attached LegacyAIPrimeFlow class **ONLY** as the "Few-Shot Example" or "Style Guide." Do not hardcode this class into the app. Instead, teach the system: *"When the user asks for an agent, write code that looks like THIS."*

⠀**Infrastructure:**
* Docker Compose with:
  * postgres (to store the agent definitions and run logs).
  * redis (for task queues).
  * agent-runner (a Python environment pre-installed with crewai[tools], pandas, etc., ready to execute the dynamic code).

⠀**Input Data:**

LEGACY AI PRIME AGENT CLASS
# ============================================================================
@persist
class LegacyAIPrimeFlow(Flow[AgentState]):
    """
    LegacyAI Prime - Production-Ready CrewAI Agent Flow
    
    Demonstrates world-class capabilities:
    - Event-driven architecture with precise control
    - Comprehensive error handling and recovery
    - Full observability and monitoring
    - Enterprise-grade tool integration
    - Cost-aware execution with limits
    - Human-in-the-loop support
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__()
        self.config = config or AgentConfig()
        self.memory = LongTermMemory() if self.config.memory_enabled else None
        self.analytics = AnalyticsService()
        
        # Initialize production tools
        self.tools = self._initialize_tools()
        
        logger.info("LegacyAI Prime Flow initialized with production configuration")
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize all production tools with error handling"""
        tools = [
            EnterpriseSearchTool(),
            CodeAnalysisTool(),
            DataVisualizationTool(),
            CommunicationTool()
        ]
        
        # Add crewai-tools if available
        if CREWAI_TOOLS_AVAILABLE:
            tools.extend([
                SerperDevTool(),
                DirectoryReadTool(),
                FileReadTool(),
                ScrapeWebsiteTool(),
                CodeInterpreterTool()
            ])
        
        logger.info(f"Initialized {len(tools)} tools")
        return tools
    
    @start()
    async def initialize_execution(self, inputs: Dict[str, Any]) -> AgentState:
        """Initialize execution with state validation"""
        try:
            # Set initial state
            self.state.task_id = inputs.get('task_id', f"task_{datetime.now().timestamp()}")
            self.state.status = "initializing"
            self.state.metadata.update(inputs)
            
            logger.info(f"Starting execution for task: {self.state.task_id}")
            
            # Validate inputs
            if not self._validate_inputs(inputs):
                raise ValueError("Invalid inputs provided")
            
            # Initialize monitoring
            self.analytics.start_session(self.state.task_id)
            
            return self.state
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            self.state.status = "error"
            self.state.error_count += 1
            return self.state
    
    @listen("initialize_execution")
    async def analyze_requirements(self, state: AgentState) -> AgentState:
        """Analyze task requirements and plan execution"""
        try:
            self.state.status = "analyzing"
            
            # Create specialized agents for different tasks
            researcher = self._create_researcher_agent()
            analyst = self._create_analyst_agent()
            implementer = self._create_implementer_agent()
            
            # Define analysis tasks
            analysis_tasks = [
                Task(
                    description=f"Analyze requirements: {state.metadata.get('task', 'Unknown task')}",
                    expected_output="Detailed analysis with success criteria and risks",
                    agent=researcher,
                    async_execution=True
                ),
                Task(
                    description="Evaluate technical feasibility and resource requirements",
                    expected_output="Feasibility assessment with resource estimates",
                    agent=analyst,
                    async_execution=True
                )
            ]
            
            # Create analysis crew
            analysis_crew = Crew(
                agents=[researcher, analyst],
                tasks=analysis_tasks,
                process=Process.parallel,
                verbose=self.config.verbose,
                memory=True
            )
            
            # Execute analysis
            analysis_result = await analysis_crew.kickoff_async(inputs=state.metadata)
            
            # Update state
            self.state.progress = 25.0
            self.state.confidence = min(self.state.confidence + 0.2, 1.0)
            self.state.results['analysis'] = analysis_result
            
            logger.info("Requirements analysis completed")
            return self.state
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            self.state.error_count += 1
            return self.state
    
    @listen("analyze_requirements")
    async def execute_main_task(self, state: AgentState) -> AgentState:
        """Execute the main task with specialized agents"""
        try:
            self.state.status = "executing"
            
            # Get task-specific implementation
            task_type = state.metadata.get('task_type', 'general')
            crew = self._create_execution_crew(task_type)
            
            # Execute with monitoring
            execution_result = await crew.kickoff_async(
                inputs={
                    **state.metadata,
                    'analysis': state.results.get('analysis', '')
                }
            )
            
            # Update state
            self.state.progress = 75.0
            self.state.confidence = min(self.state.confidence + 0.3, 1.0)
            self.state.results['execution'] = execution_result
            
            logger.info("Main task execution completed")
            return self.state
            
        except Exception as e:
            logger.error(f"Main execution failed: {str(e)}")
            self.state.error_count += 1
            return self.state
    
    @router(execute_main_task)
    def determine_next_steps(self) -> str:
        """Determine next steps based on execution results"""
        if self.state.error_count > 3:
            return "escalate_to_human"
        elif self.state.confidence < 0.5:
            return "retry_with_different_approach"
        elif self.state.progress >= 75.0:
            return "finalize_results"
        else:
            return "continue_execution"
    
    @listen("finalize_results")
    async def finalize_and_report(self, state: AgentState) -> AgentState:
        """Finalize results and generate comprehensive report"""
        try:
            self.state.status = "finalizing"
            
            # Create reporting agent
            reporter = self._create_reporter_agent()
            
            # Generate final report
            report_task = Task(
                description="Create comprehensive final report with all findings",
                expected_output="Structured report with executive summary, details, and recommendations",
                agent=reporter,
                output_file=f"reports/{self.state.task_id}_final_report.md"
            )
            
            report_crew = Crew(
                agents=[reporter],
                tasks=[report_task],
                verbose=self.config.verbose
            )
            
            report_result = await report_crew.kickoff_async(inputs=state.results)
            
            # Send notification
            notification_tool = CommunicationTool()
            await self._send_completion_notification(notification_tool)
            
            # Final state update
            self.state.progress = 100.0
            self.state.status = "completed"
            self.state.results['final_report'] = report_result
            
            logger.info("Task finalized successfully")
            return self.state
            
        except Exception as e:
            logger.error(f"Finalization failed: {str(e)}")
            self.state.error_count += 1
            return self.state
    
    @listen(or_("escalate_to_human", "retry_with_different_approach"))
    async def handle_error_recovery(self, state: AgentState) -> AgentState:
        """Handle error recovery and human escalation"""
        try:
            self.state.status = "recovering"
            
            if "escalate_to_human" in state.status:
                await self._escalate_to_human()
            else:
                # Retry with different parameters
                state.metadata['retry_attempt'] = state.metadata.get('retry_attempt', 0) + 1
                return await self.analyze_requirements(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Error recovery failed: {str(e)}")
            self.state.status = "failed"
            return state
    
    # ========================================================================
    # AGENT CREATION METHODS - SPECIALIZED ROLES
    # ========================================================================
    
    def _create_researcher_agent(self) -> Agent:
        """Create specialized research agent"""
        return Agent(
            role="Senior Research Analyst",
            goal="Conduct comprehensive research and data gathering",
            backstory="""You are an expert research analyst with 10+ years of experience 
            in gathering and synthesizing information from diverse sources. You excel at 
            finding relevant data, identifying trends, and providing actionable insights.""",
            tools=self.tools[:4],  # Research-specific tools
            llm=LLM(
                model="gpt-4o",
                temperature=self.config.temperature,
                max_tokens=4000
            ),
            max_iter=self.config.max_iterations,
            max_rpm=self.config.max_rpm,
            allow_delegation=self.config.allow_delegation,
            verbose=self.config.verbose,
            memory=True
        )
    
    def _create_analyst_agent(self) -> Agent:
        """Create specialized analysis agent"""
        return Agent(
            role="Technical Analyst",
            goal="Analyze requirements and assess technical feasibility",
            backstory="""You are a seasoned technical analyst with deep expertise in 
            system architecture, feasibility assessment, and risk analysis. You provide 
            clear, actionable recommendations based on thorough technical evaluation.""",
            tools=self.tools[2:5],  # Analysis-specific tools
            llm=LLM(
                model="gpt-4o",
                temperature=0.3,  # Lower temperature for analysis
                max_tokens=3000
            ),
            max_iter=self.config.max_iterations,
            max_rpm=self.config.max_rpm,
            allow_delegation=False,
            verbose=self.config.verbose,
            memory=True
        )
    
    def _create_implementer_agent(self) -> Agent:
        """Create specialized implementation agent"""
        return Agent(
            role="Implementation Specialist",
            goal="Execute tasks with high quality and precision",
            backstory="""You are an expert implementer known for delivering high-quality 
            solutions with attention to detail and best practices. You excel at turning 
            analysis into actionable results.""",
            tools=self.tools,
            llm=LLM(
                model="gpt-4o",
                temperature=self.config.temperature,
                max_tokens=4000
            ),
            max_iter=self.config.max_iterations,
            max_rpm=self.config.max_rpm,
            allow_delegation=self.config.allow_delegation,
            verbose=self.config.verbose,
            memory=True
        )
    
    def _create_reporter_agent(self) -> Agent:
        """Create specialized reporting agent"""
        return Agent(
            role="Documentation & Reporting Specialist",
            goal="Create comprehensive, professional reports and documentation",
            backstory="""You are an expert technical writer specializing in creating 
            clear, comprehensive reports and documentation. You excel at organizing 
            complex information into accessible, professional formats.""",
            tools=[CommunicationTool(), DataVisualizationTool()],
            llm=LLM(
                model="gpt-4o",
                temperature=0.2,  # Low temperature for consistency
                max_tokens=4000
            ),
            max_iter=15,  # Lower for reporting
            max_rpm=30,
            allow_delegation=False,
            verbose=self.config.verbose,
            memory=True
        )
    
    def _create_execution_crew(self, task_type: str) -> Crew:
        """Create task-specific execution crew"""
        agents = [self._create_implementer_agent()]
        
        # Add specialized agents based on task type
        if task_type == "development":
            agents.append(self._create_analyst_agent())
        elif task_type == "research":
            agents.append(self._create_researcher_agent())
        
        tasks = [
            Task(
                description=f"Execute {task_type} task: {self.state.metadata.get('task', '')}",
                expected_output="High-quality results with documented process",
                agent=agents[0],
                async_execution=len(agents) > 1
            )
        ]
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.parallel if len(agents) > 1 else Process.sequential,
            verbose=self.config.verbose,
            memory=True,
            planning=True
        )
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        required_fields = ['task', 'task_type']
        return all(field in inputs for field in required_fields)
    
    async def _send_completion_notification(self, notification_tool: CommunicationTool):
        """Send task completion notification"""
        try:
            message = f"""
Task {self.state.task_id} completed successfully.
Status: {self.state.status}
Progress: {self.state.progress}%
Confidence: {self.state.confidence:.2f}
Errors: {self.state.error_count}
Results available in: reports/{self.state.task_id}_final_report.md
            """.strip()
            
            await notification_tool._run(
                message=message,
                channel="email",
                recipients=self.state.metadata.get('notification_email', '')
            )
            
        except Exception as e:
            logger.error(f"Notification failed: {str(e)}")
    
    async def _escalate_to_human(self):
        """Escalate task to human supervisor"""
        try:
            escalation_tool = CommunicationTool()
            message = f"""
URGENT: Task {self.state.task_id} requires human intervention.
Status: {self.state.status}
Error Count: {self.state.error_count}
Last Error: {self.state.metadata.get('last_error', 'Unknown')}
Please review and provide guidance.
            """.strip()
            
            await escalation_tool._run(
                message=message,
                channel="teams",
                recipients=self.state.metadata.get('escalation_contact', '')
            )
            
            self.state.status = "escalated"
            
        except Exception as e:
            logger.error(f"Escalation failed: {str(e)}")
# ============================================================================
# SUPPORTING CLASSES
# ============================================================================
class AnalyticsService:
    """Analytics and monitoring service"""
    
    def __init__(self):
        self.metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_execution_time': 0,
            'total_cost': 0.0,
            'average_confidence': 0.0
        }
    
    def start_session(self, task_id: str):
        """Start tracking session"""
        self.current_session = {
            'task_id': task_id,
            'start_time': datetime.now(),
            'events': []
        }
    
    def record_call(self, duration: float, tokens: int, cost: float):
        """Record LLM call metrics"""
        self.metrics['total_cost'] += cost
        if 'events' in self.current_session:
            self.current_session['events'].append({
                'type': 'llm_call',
                'duration': duration,
                'tokens': tokens,
                'cost': cost,
                'timestamp': datetime.now()
            })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current analytics metrics"""
        return self.metrics
class RateLimitError(Exception):
    """Custom exception for rate limiting"""
    pass
# ============================================================================
# MAIN EXECUTION
# ============================================================================
def create_production_config() -> AgentConfig:
    """Create production-ready configuration"""
    return AgentConfig(
        max_iterations=25,
        max_rpm=60,
        timeout=300,
        temperature=0.7,
        allow_delegation=True,
        verbose=True,
        memory_enabled=True,
        cache_enabled=True
    )
def create_development_config() -> AgentConfig:
    """Create development-friendly configuration"""
    return AgentConfig(
        max_iterations=10,
        max_rpm=30,
        timeout=180,
        temperature=0.9,  # Higher creativity for development
        allow_delegation=True,
        verbose=True,
        memory_enabled=True,
        cache_enabled=False  # Disable cache for testing
    )
async def main():
    """Main execution function with comprehensive example"""
    print("🚀 LegacyAI Prime - World-Class CrewAI Agent Template")
    print("=" * 60)
    
    # Initialize with production configuration
    config = create_production_config()
    
    # Create and configure the flow
    flow = LegacyAIPrimeFlow(config)
    
    # Example execution
    sample_inputs = {
        'task_id': f"demo_{datetime.now().timestamp()}",
        'task': 'Analyze current AI agent landscape and provide strategic recommendations',
        'task_type': 'research',
        'notification_email': 'team@example.com',
        'escalation_contact': 'supervisor@example.com',
        'max_cost': 5.0  # Maximum cost in USD
    }
    
    try:
        # Initialize OpenTelemetry for production monitoring
        OpenTelemetry.init(
            service_name="legacyai-prime-agent",
            endpoint=os.getenv("OTEL_ENDPOINT", "http://localhost:4317")
        )
        
        logger.info("Starting LegacyAI Prime execution")
        result = await flow.kickoff(inputs=sample_inputs)
        
        # Print results
        print("\n✅ EXECUTION COMPLETED SUCCESSFULLY")
        print(f"📊 Final Status: {result.status}")
        print(f"📈 Progress: {result.progress}%")
        print(f"🎯 Confidence: {result.confidence:.2f}")
        print(f"🔧 Errors: {result.error_count}")
        print(f"📄 Results: {len(result.results)} items generated")
        
        # Show analytics
        analytics = flow.analytics.get_metrics()
        print(f"\n📈 ANALYTICS SUMMARY:")
        print(f"   Total Cost: ${analytics['total_cost']:.4f}")
        print(f"   Success Rate: {analytics['successful_tasks']/(analytics['total_tasks'] or 1)*100:.1f}%")
        
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        print(f"\n❌ EXECUTION FAILED: {str(e)}")
        print("🔍 Check logs for detailed error information")
if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Run with asyncio
    asyncio.run(main())
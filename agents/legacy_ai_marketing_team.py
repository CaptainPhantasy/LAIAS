
from crewai import Agent, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start
from crewai.flow.persistence import persist
from pydantic import BaseModel, Field
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class MarketingState(BaseModel):
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    error_count: int = Field(default=0)
    last_error: str = Field(default=None)
    progress: float = Field(default=0.0)
    linkedin_content: str = Field(default="")
    research_trends: str = Field(default="")
    post_engagement: str = Field(default="")

@persist()
class LegacyAIMarketingFlow(Flow[MarketingState]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = self.auto_select_tools()

    def _create_content_creator(self) -> Agent:
        return Agent(
            role="Content Creator",
            goal="Craft humorous and engaging LinkedIn content avoiding corporate jargon.",
            backstory="Expert in social media marketing with a knack for humor and engaging content.",
            tools=self.tools,
            llm=LLM(model="openai/gpt-4o", temperature=0.8)
        )

    def _create_trend_researcher(self) -> Agent:
        return Agent(
            role="Trend Researcher",
            goal="Identify current marketing trends relevant to Legacy AI.",
            backstory="Data-driven marketer with expertise in trend analysis.",
            tools=self.tools,
            llm=LLM(model="openai/gpt-4o", temperature=0.7)
        )

    def _create_engagement_specialist(self) -> Agent:
        return Agent(
            role="Engagement Specialist",
            goal="Generate engaging posts with self-deprecating humor.",
            backstory="Seasoned marketer with a talent for creating viral content.",
            tools=self.tools,
            llm=LLM(model="openai/gpt-4o", temperature=0.8)
        )

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> MarketingState:
        self.state.task_id = inputs.get("task_id", "marketing_001")
        self.state.status = "initializing"
        logger.info("Initializing marketing flow", task_id=self.state.task_id)
        return self.state

    @listen("initialize")
    async def create_linkedin_content(self, state: MarketingState) -> MarketingState:
        try:
            self.state.status = "creating_content"
            content_creator = self._create_content_creator()
            task_description = "Create LinkedIn content incorporating humor and self-deprecation."
            task = Task(
                description=task_description,
                agent=content_creator
            )
            crew = Crew(agents=[content_creator], tasks=[task], process=Process.sequential)
            result = await crew.kickoff_async()
            self.state.linkedin_content = str(result)

            logger.info("LinkedIn content created", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Content creation failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "failed"
            return self.state

    @listen("create_linkedin_content")
    async def research_trends(self, state: MarketingState) -> MarketingState:
        try:
            self.state.status = "researching_trends"
            trend_researcher = self._create_trend_researcher()
            task_description = "Research current marketing trends for AI products."
            task = Task(
                description=task_description,
                agent=trend_researcher
            )
            crew = Crew(agents=[trend_researcher], tasks=[task], process=Process.sequential)
            result = await crew.kickoff_async()
            self.state.research_trends = str(result)

            logger.info("Trend research completed", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Trend research failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "failed"
            return self.state

    @listen("research_trends")
    async def generate_post_engagement(self, state: MarketingState) -> MarketingState:
        try:
            self.state.status = "generating_engagement"
            engagement_specialist = self._create_engagement_specialist()
            task_description = "Generate engaging posts with humor and self-deprecation."
            task = Task(
                description=task_description,
                agent=engagement_specialist
            )
            crew = Crew(agents=[engagement_specialist], tasks=[task], process=Process.sequential)
            result = await crew.kickoff_async()
            self.state.post_engagement = str(result)

            logger.info("Post engagement generated", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Post engagement generation failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "failed"
            return self.state

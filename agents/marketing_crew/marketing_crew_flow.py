
from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start
from crewai.flow.persistence import persist
from pydantic import BaseModel, Field
from typing import Dict, Any
import structlog
import yaml
from pathlib import Path

logger = structlog.get_logger()

# Load voice guide
STYLE_GUIDE_PATH = Path(__file__).parent / "style_guide" / "VOICE_AND_STYLE.md"
AGENTS_CONFIG_PATH = Path(__file__).parent / "agents.yaml"

def load_style_guide() -> str:
    if STYLE_GUIDE_PATH.exists():
        return STYLE_GUIDE_PATH.read_text()
    return ""

def load_agents_config() -> Dict[str, Any]:
    if AGENTS_CONFIG_PATH.exists():
        with open(AGENTS_CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return {}

class MarketingState(BaseModel):
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    error_count: int = Field(default=0)
    last_error: str = Field(default=None)
    progress: float = Field(default=0.0)
    input_content: str = Field(default="")  # Raw input from user
    content_drafts: str = Field(default="")
    social_media_posts: str = Field(default="")
    final_content: str = Field(default="")

@persist
class MarketingCrewFlow(Flow[MarketingState]):
    def __init__(self):
        super().__init__()
        self.style_guide = load_style_guide()
        self.agents_config = load_agents_config()

    def _create_content_writer(self) -> Agent:
        config = self.agents_config.get("CONTENT_WRITER", {})
        return Agent(
            role=config.get("role", "CONTENT_WRITER"),
            goal=config.get("goal", "Expand rough ideas into polished content"),
            backstory=config.get("backstory", ""),
            llm=LLM(model="openai/gpt-4o", temperature=0.8)
        )

    def _create_social_media_manager(self) -> Agent:
        config = self.agents_config.get("SOCIAL_MEDIA_MANAGER", {})
        return Agent(
            role=config.get("role", "SOCIAL_MEDIA_MANAGER"),
            goal=config.get("goal", "Reformat content for social media platforms"),
            backstory=config.get("backstory", ""),
            llm=LLM(model="openai/gpt-4o", temperature=0.8)
        )

    def _create_brand_coordinator(self) -> Agent:
        config = self.agents_config.get("BRAND_COORDINATOR", {})
        return Agent(
            role=config.get("role", "BRAND_COORDINATOR"),
            goal=config.get("goal", "Ensure voice consistency"),
            backstory=config.get("backstory", ""),
            llm=LLM(model="openai/gpt-4o", temperature=0.5)
        )

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> MarketingState:
        self.state.task_id = inputs.get("task_id", "marketing_001")
        self.state.status = "initialized"
        logger.info("Marketing flow initialized", task_id=self.state.task_id)
        return self.state

    @listen("initialize")
    async def create_content(self, state: MarketingState) -> MarketingState:
        try:
            self.state.status = "creating_content"
            content_writer = self._create_content_writer()

            input_text = self.state.input_content or "No input provided"
            task = Task(
                description=f"""
Transform this rough content into polished, authentic prose.

STYLE GUIDE:
{self.style_guide[:2000]}

INPUT CONTENT:
{input_text}

Write in the Legacy AI voice. No corporate speak. No fake enthusiasm. 
Sound like a real human talking to a smart friend.
""",
                expected_output="Polished content in Legacy AI voice",
                agent=content_writer
            )

            crew = Crew(agents=[content_writer], tasks=[task], process=Process.sequential)
            result = await crew.kickoff_async()

            self.state.content_drafts = str(result)
            self.state.progress += 33.3
            self.state.status = "content_created"

            logger.info("Content creation completed", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Content creation failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "failed"
            return self.state

    @listen("create_content")
    async def manage_social_media(self, state: MarketingState) -> MarketingState:
        try:
            self.state.status = "managing_social_media"
            social_media_manager = self._create_social_media_manager()

            task = Task(
                description="Reformat content for social media platforms",
                expected_output="Social media posts",
                agent=social_media_manager
            )

            crew = Crew(agents=[social_media_manager], tasks=[task], process=Process.sequential)
            result = await crew.kickoff_async()

            self.state.social_media_posts = str(result)
            self.state.progress += 33.3
            self.state.status = "social_media_managed"

            logger.info("Social media management completed", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Social media management failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "failed"
            return self.state

    @listen("manage_social_media")
    async def coordinate_brand(self, state: MarketingState) -> MarketingState:
        try:
            self.state.status = "coordinating_brand"
            brand_coordinator = self._create_brand_coordinator()

            task = Task(
                description="Review and finalize all content",
                expected_output="Final approved content",
                agent=brand_coordinator
            )

            crew = Crew(agents=[brand_coordinator], tasks=[task], process=Process.sequential)
            result = await crew.kickoff_async()

            self.state.final_content = str(result)
            self.state.progress = 100.0
            self.state.status = "completed"

            logger.info("Brand coordination completed", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Brand coordination failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "failed"
            return self.state

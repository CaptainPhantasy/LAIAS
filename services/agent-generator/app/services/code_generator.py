"""
Code Generator Service for Agent Generator.

Orchestrates the code generation process using LLM service,
template management, and validation.
"""

from typing import Dict, Any, List, Optional
import structlog

from app.config import settings
from app.services.llm_service import get_llm_service
from app.services.validator import get_validator
from app.services.template_service import get_template_service
from app.prompts.few_shot_examples import get_few_shot_examples
from app.models.responses import (
    GenerateAgentResponse,
    AgentInfo,
    ValidationResult
)
from app.utils.helpers import (
    generate_agent_id,
    calculate_cost_estimate,
    sanitize_agent_name,
    format_mermaid_diagram
)
from app.utils.exceptions import LLMServiceException

logger = structlog.get_logger()


class CodeGenerator:
    """
    Service for generating CrewAI agent code.

    Coordinates:
    - LLM service for code generation
    - Template service for pattern reference
    - Validator for code quality assurance
    """

    def __init__(self):
        """Initialize the code generator."""
        self.llm_service = get_llm_service()
        self.validator = get_validator()
        self.template_service = get_template_service()
        self.total_generated = 0

    async def generate_agent(
        self,
        description: str,
        agent_name: str,
        complexity: str = "moderate",
        task_type: str = "general",
        tools_requested: Optional[List[str]] = None,
        llm_provider: str = "openai",
        model: Optional[str] = None,
        include_memory: bool = True,
        include_analytics: bool = True,
        max_agents: int = 4
    ) -> GenerateAgentResponse:
        """
        Generate a complete CrewAI agent from description.

        Args:
            description: Natural language description
            agent_name: Name for the flow class
            complexity: Complexity level
            task_type: Task category
            tools_requested: Specific tools to include
            llm_provider: LLM provider
            model: Model override
            include_memory: Enable memory
            include_analytics: Include analytics
            max_agents: Maximum agents

        Returns:
            GenerateAgentResponse with complete code and metadata
        """
        from datetime import datetime

        # Sanitize and validate inputs
        agent_name = sanitize_agent_name(agent_name)

        logger.info(
            "Starting agent generation",
            agent_name=agent_name,
            complexity=complexity,
            task_type=task_type
        )

        # Get few-shot examples if enabled
        few_shot_examples = []
        if settings.enable_few_shot:
            from app.prompts.few_shot_examples import FEW_SHOT_SELECTOR
            few_shot_examples = FEW_SHOT_SELECTOR.get_examples(complexity, task_type, count=2)

        # Generate code via LLM
        try:
            generation_result = await self.llm_service.generate_code(
                description=description,
                agent_name=agent_name,
                complexity=complexity,
                task_type=task_type,
                tools_requested=tools_requested,
                provider=llm_provider,
                model=model,
                include_memory=include_memory,
                include_analytics=include_analytics,
                max_agents=max_agents,
                few_shot_examples=few_shot_examples
            )
        except LLMServiceException as e:
            logger.error("LLM generation failed", error=str(e))
            raise

        # Extract and validate generated code
        flow_code = generation_result.get("flow_code", "")
        state_class = generation_result.get("state_class", "")
        agents_yaml = generation_result.get("agents_yaml", "")
        requirements = generation_result.get("requirements", [])
        agents_info = generation_result.get("agents_info", [])
        flow_diagram = generation_result.get("flow_diagram", "")

        # Validate the generated code
        validation = self.validator.validate_code(
            code=flow_code,
            check_pattern_compliance=True,
            check_syntax=True
        )

        # Estimate cost
        cost_estimate = calculate_cost_estimate(
            complexity=complexity,
            agent_count=len(agents_info),
            model=model or settings.default_model
        )

        # Build agent info objects
        agent_info_objects = []
        for info in agents_info:
            agent_info_objects.append(AgentInfo(
                role=info.get("role", "Specialist"),
                goal=info.get("goal", ""),
                tools=info.get("tools", []),
                llm_config=info.get("llm_config", {}),
                backstory=info.get("backstory")
            ))

        # Build response
        response = GenerateAgentResponse(
            agent_id=generate_agent_id(),
            agent_name=agent_name,
            flow_code=flow_code,
            agents_yaml=agents_yaml,
            state_class=state_class,
            requirements=requirements or ["crewai[tools]>=0.80.0", "pydantic>=2.5.0", "structlog>=24.1.0"],
            estimated_cost_per_run=cost_estimate["estimated_cost_usd"],
            complexity_score=self._calculate_complexity_score(complexity, max_agents),
            agents_created=agent_info_objects,
            tools_included=list(set(tool for info in agents_info for tool in info.get("tools", []))),
            flow_diagram=flow_diagram,
            validation_status=ValidationResult(**validation),
            created_at=datetime.utcnow()
        )

        self.total_generated += 1
        logger.info(
            "Agent generation complete",
            agent_id=response.agent_id,
            is_valid=validation["is_valid"],
            compliance=validation["pattern_compliance_score"]
        )

        return response

    def _calculate_complexity_score(self, complexity: str, agent_count: int) -> int:
        """Calculate numeric complexity score (1-10)."""
        base_scores = {"simple": 3, "moderate": 5, "complex": 8}
        base = base_scores.get(complexity, 5)
        # Adjust by agent count
        adjustment = (agent_count - 4) // 2
        return max(1, min(10, base + adjustment))

    async def regenerate_with_feedback(
        self,
        agent_id: str,
        feedback: str,
        previous_code: str
    ) -> GenerateAgentResponse:
        """
        Regenerate agent based on feedback.

        Args:
            agent_id: Original agent ID
            feedback: User feedback for improvement
            previous_code: Previous code to improve

        Returns:
            Updated GenerateAgentResponse
        """
        from datetime import datetime

        logger.info("Regenerating with feedback", agent_id=agent_id)

        # Create refinement prompt
        refinement_prompt = f"""Improve the following agent code based on this feedback:

FEEDBACK:
{feedback}

PREVIOUS CODE:
{previous_code[:2000]}...

Generate improved code addressing the feedback while maintaining Godzilla pattern."""

        # Use LLM service for regeneration
        generation_result = await self.llm_service.generate_code(
            description=refinement_prompt,
            agent_name="RefinedFlow",
            complexity="moderate",
            task_type="general",
            tools_requested=None,
            provider=settings.effective_llm_provider
        )

        # Build response
        validation = self.validator.validate_code(
            code=generation_result.get("flow_code", ""),
            check_pattern_compliance=True
        )

        return GenerateAgentResponse(
            agent_id=agent_id,
            agent_name="RefinedFlow",
            flow_code=generation_result.get("flow_code", ""),
            agents_yaml=generation_result.get("agents_yaml", ""),
            state_class=generation_result.get("state_class", ""),
            requirements=generation_result.get("requirements", []),
            estimated_cost_per_run=0.1,
            complexity_score=5,
            agents_created=[],
            tools_included=[],
            validation_status=ValidationResult(**validation),
            created_at=datetime.utcnow()
        )


# Global service instance
_code_generator: Optional[CodeGenerator] = None


def get_code_generator() -> CodeGenerator:
    """Get or create code generator instance."""
    global _code_generator
    if _code_generator is None:
        _code_generator = CodeGenerator()
    return _code_generator

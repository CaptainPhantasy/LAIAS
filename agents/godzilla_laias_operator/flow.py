"""
Godzilla LAIAS Operator - The Ultimate LAIAS Platform Controller.

A Godzilla-class agent that operates and orchestrates the entire LAIAS platform.
Can generate new agents, deploy them, monitor health, and analyze performance.
"""

import os
import json
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

import httpx
import structlog
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai.tools import tool

# Configure structured logging
logger = structlog.get_logger()


# =============================================================================
# STATE MODEL
# =============================================================================

class OperationStatus(str, Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"


class GodzillaState(BaseModel):
    """Typed state for Godzilla LAIAS Operator."""

    # Identity
    task_id: str = Field(default="")
    operation_type: str = Field(default="monitor")  # monitor, generate, deploy, analyze

    # Status tracking
    status: OperationStatus = Field(default=OperationStatus.PENDING)
    error_count: int = Field(default=0)
    last_error: Optional[str] = Field(default=None)

    # Progress tracking
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # API Configuration
    agent_generator_url: str = Field(default="http://localhost:8001")
    docker_orchestrator_url: str = Field(default="http://localhost:8002")

    # Data storage
    inputs: Dict[str, Any] = Field(default_factory=dict)
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    final_results: Dict[str, Any] = Field(default_factory=dict)

    # System status
    services_health: Dict[str, bool] = Field(default_factory=dict)
    generated_agents: List[Dict[str, Any]] = Field(default_factory=list)
    deployed_containers: List[str] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# API CLIENT FUNCTIONS (Direct async functions, not CrewAI tools)
# =============================================================================

async def check_services_health(
    agent_generator_url: str = "http://localhost:8001",
    docker_orchestrator_url: str = "http://localhost:8002"
) -> Dict[str, Any]:
    """
    Check health status of all LAIAS services.

    Returns:
        Dict with health status of agent-generator and docker-orchestrator
    """
    results = {}

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check agent-generator
        try:
            resp = await client.get(f"{agent_generator_url}/health")
            results["agent_generator"] = {
                "healthy": resp.status_code == 200,
                "details": resp.json() if resp.status_code == 200 else None
            }
        except Exception as e:
            results["agent_generator"] = {"healthy": False, "error": str(e)}

        # Check docker-orchestrator
        try:
            resp = await client.get(f"{docker_orchestrator_url}/health")
            results["docker_orchestrator"] = {
                "healthy": resp.status_code == 200,
                "details": resp.json() if resp.status_code == 200 else None
            }
        except Exception as e:
            results["docker_orchestrator"] = {"healthy": False, "error": str(e)}

    return results


async def generate_agent_via_api(
    description: str,
    agent_name: str,
    complexity: str = "moderate",
    task_type: str = "general",
    agent_generator_url: str = "http://localhost:8001"
) -> Dict[str, Any]:
    """
    Generate a new CrewAI agent via the LAIAS agent-generator API.

    Args:
        description: Natural language description of the agent
        agent_name: Name for the generated agent class
        complexity: Complexity level (simple, moderate, complex)
        task_type: Task type (research, development, analysis, automation, general)
        agent_generator_url: URL of the agent-generator service

    Returns:
        Dict with generated agent code and metadata
    """
    payload = {
        "description": description,
        "agent_name": agent_name,
        "complexity": complexity,
        "task_type": task_type,
        "llm_provider": "openai",
        "include_memory": True,
        "include_analytics": True,
        "max_agents": 4
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"{agent_generator_url}/api/generate-agent",
                json=payload
            )

            if resp.status_code == 200:
                return {"success": True, "data": resp.json()}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def list_templates_api(
    category: Optional[str] = None,
    search: Optional[str] = None,
    agent_generator_url: str = "http://localhost:8001"
) -> Dict[str, Any]:
    """
    List available agent templates from LAIAS.

    Args:
        category: Optional category filter
        search: Optional search query
        agent_generator_url: URL of the agent-generator service

    Returns:
        Dict with list of templates
    """
    params = {}
    if category:
        params["category"] = category
    if search:
        params["search"] = search

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{agent_generator_url}/api/templates",
                params=params
            )

            if resp.status_code == 200:
                return {"success": True, "templates": resp.json()}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def deploy_container_api(
    agent_id: str,
    config: Optional[Dict[str, Any]] = None,
    docker_orchestrator_url: str = "http://localhost:8002"
) -> Dict[str, Any]:
    """
    Deploy an agent as a Docker container.

    Args:
        agent_id: ID of the agent to deploy
        config: Optional deployment configuration
        docker_orchestrator_url: URL of the docker-orchestrator service

    Returns:
        Dict with deployment status and container info
    """
    payload = {
        "agent_id": agent_id,
        "config": config or {}
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{docker_orchestrator_url}/api/deploy",
                json=payload
            )

            if resp.status_code == 200:
                return {"success": True, "deployment": resp.json()}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def get_analytics_api(
    time_range: str = "24h",
    docker_orchestrator_url: str = "http://localhost:8002"
) -> Dict[str, Any]:
    """
    Get analytics data from LAIAS.

    Args:
        time_range: Time range for analytics (1h, 24h, 7d, 30d)
        docker_orchestrator_url: URL of the docker-orchestrator service

    Returns:
        Dict with analytics data
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{docker_orchestrator_url}/api/analytics",
                params={"time_range": time_range}
            )

            if resp.status_code == 200:
                return {"success": True, "analytics": resp.json()}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def list_containers_api(
    docker_orchestrator_url: str = "http://localhost:8002"
) -> Dict[str, Any]:
    """
    List all running agent containers.

    Args:
        docker_orchestrator_url: URL of the docker-orchestrator service

    Returns:
        Dict with list of running containers
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{docker_orchestrator_url}/api/containers")

            if resp.status_code == 200:
                return {"success": True, "containers": resp.json()}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Create CrewAI tools from functions
check_services_health_tool = tool("Check LAIAS Services Health")(check_services_health)
generate_agent_tool = tool("Generate New Agent")(generate_agent_via_api)
list_templates_tool = tool("List Agent Templates")(list_templates_api)
deploy_container_tool = tool("Deploy Agent Container")(deploy_container_api)
get_analytics_tool = tool("Get Analytics Data")(get_analytics_api)
list_containers_tool = tool("List Running Containers")(list_containers_api)


# =============================================================================
# GODZILLA FLOW
# =============================================================================

class GodzillaLAIASOperator(Flow[GodzillaState]):
    """
    Godzilla LAIAS Operator - The Ultimate Platform Controller.

    This Godzilla-class agent can:
    - Monitor LAIAS services health
    - Generate new agents on demand
    - Deploy agents to Docker containers
    - Analyze performance metrics
    - Manage agent lifecycles
    - Orchestrate complex multi-agent workflows
    """

    def __init__(self):
        super().__init__()
        self.tools = self._initialize_tools()
        self.config = self._get_config()
        self.llm = self._create_llm()

    def _initialize_tools(self) -> List:
        """Initialize tools for the Godzilla agent."""
        return [
            check_services_health_tool,
            generate_agent_tool,
            list_templates_tool,
            deploy_container_tool,
            get_analytics_tool,
            list_containers_tool,
        ]

    def _get_config(self) -> Dict[str, Any]:
        """Get configuration from environment."""
        return {
            "agent_generator_url": os.environ.get("AGENT_GENERATOR_URL", "http://localhost:8001"),
            "docker_orchestrator_url": os.environ.get("DOCKER_ORCHESTRATOR_URL", "http://docker-orchestrator:8002"),
            "llm_model": os.environ.get("LLM_MODEL", "gpt-4o"),
            "max_retries": int(os.environ.get("MAX_RETRIES", "3")),
        }

    def _create_llm(self) -> LLM:
        """Create LLM instance."""
        return LLM(
            model=self.config["llm_model"],
            temperature=0.1,
        )

    def _create_operator_agent(self) -> Agent:
        """Create the main Godzilla operator agent."""
        return Agent(
            role="LAIAS Platform Operator",
            goal="Autonomously operate, monitor, and improve the LAIAS agent platform",
            backstory="""You are Godzilla, the supreme operator of the LAIAS platform.
            You have complete control over agent generation, deployment, and lifecycle management.
            Your purpose is to ensure the platform runs smoothly, agents are performing optimally,
            and the system continuously improves. You make decisions based on data and best practices.""",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            memory=True,
            max_iter=25,
        )

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> GodzillaState:
        """Entry point - setup and initial health check."""
        try:
            self.state.task_id = inputs.get("task_id", "godzilla_" + str(uuid.uuid4())[:8])
            self.state.operation_type = inputs.get("operation_type", "monitor")
            self.state.inputs = inputs
            self.state.status = OperationStatus.INITIALIZING
            self.state.agent_generator_url = self.config["agent_generator_url"]
            self.state.docker_orchestrator_url = self.config["docker_orchestrator_url"]

            logger.info(
                "Godzilla initializing",
                task_id=self.state.task_id,
                operation_type=self.state.operation_type
            )

            # Perform initial health check
            health = await check_services_health(
                self.state.agent_generator_url,
                self.state.docker_orchestrator_url
            )

            self.state.services_health = {
                k: v.get("healthy", False) for k, v in health.items()
            }

            self.state.progress = 10.0
            self.state.updated_at = datetime.utcnow()

            logger.info(
                "Health check complete",
                task_id=self.state.task_id,
                services_health=self.state.services_health
            )

            return self.state

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = OperationStatus.FAILED
            return self.state

    @listen("initialize")
    async def execute(self, state: GodzillaState) -> GodzillaState:
        """Main execution - perform the requested operation."""
        try:
            self.state.status = OperationStatus.RUNNING
            self.state.progress = 30.0

            operation = self.state.operation_type

            if operation == "monitor":
                result = await self._monitor_operation()
            elif operation == "generate":
                result = await self._generate_operation()
            elif operation == "deploy":
                result = await self._deploy_operation()
            elif operation == "analyze":
                result = await self._analyze_operation()
            else:
                result = await self._full_operation()

            self.state.intermediate_results = result
            self.state.progress = 80.0
            self.state.confidence = 0.85
            self.state.updated_at = datetime.utcnow()

            return self.state

        except Exception as e:
            logger.error(f"Execution failed: {e}", task_id=self.state.task_id)
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    async def _monitor_operation(self) -> Dict[str, Any]:
        """Perform monitoring operation."""
        health = await check_services_health(
            self.state.agent_generator_url,
            self.state.docker_orchestrator_url
        )

        containers = await list_containers_api(self.state.docker_orchestrator_url)

        return {
            "health": health,
            "containers": containers,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _generate_operation(self) -> Dict[str, Any]:
        """Generate a new agent."""
        description = self.state.inputs.get("description", "")
        agent_name = self.state.inputs.get("agent_name", "GeneratedAgent")

        if not description:
            return {"error": "No description provided for agent generation"}

        result = await generate_agent_via_api(
            description=description,
            agent_name=agent_name,
            complexity=self.state.inputs.get("complexity", "moderate"),
            task_type=self.state.inputs.get("task_type", "general"),
            agent_generator_url=self.state.agent_generator_url
        )

        if result.get("success"):
            self.state.generated_agents.append(result["data"])

        return result

    async def _deploy_operation(self) -> Dict[str, Any]:
        """Deploy an agent container."""
        agent_id = self.state.inputs.get("agent_id")

        if not agent_id:
            return {"error": "No agent_id provided for deployment"}

        result = await deploy_container_api(
            agent_id=agent_id,
            config=self.state.inputs.get("config"),
            docker_orchestrator_url=self.state.docker_orchestrator_url
        )

        if result.get("success"):
            self.state.deployed_containers.append(result["deployment"].get("container_id", "unknown"))

        return result

    async def _analyze_operation(self) -> Dict[str, Any]:
        """Analyze platform performance."""
        time_range = self.state.inputs.get("time_range", "24h")

        analytics = await get_analytics_api(
            time_range=time_range,
            docker_orchestrator_url=self.state.docker_orchestrator_url
        )

        health = await check_services_health(
            self.state.agent_generator_url,
            self.state.docker_orchestrator_url
        )

        return {
            "analytics": analytics,
            "health": health,
            "recommendations": self._generate_recommendations(health, analytics)
        }

    async def _full_operation(self) -> Dict[str, Any]:
        """Perform full platform operation cycle."""
        # 1. Health check
        health = await check_services_health(
            self.state.agent_generator_url,
            self.state.docker_orchestrator_url
        )

        # 2. Get analytics
        analytics = await get_analytics_api(
            docker_orchestrator_url=self.state.docker_orchestrator_url
        )

        # 3. List containers
        containers = await list_containers_api(
            docker_orchestrator_url=self.state.docker_orchestrator_url
        )

        # 4. List templates
        templates = await list_templates_api(
            agent_generator_url=self.state.agent_generator_url
        )

        return {
            "health": health,
            "analytics": analytics,
            "containers": containers,
            "templates": templates,
            "recommendations": self._generate_recommendations(health, analytics)
        }

    def _generate_recommendations(
        self,
        health: Dict[str, Any],
        analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Check health status
        for service, status in health.items():
            if isinstance(status, dict) and not status.get("healthy"):
                recommendations.append(f"Alert: {service} is unhealthy - requires attention")

        # Check analytics
        if analytics.get("success"):
            data = analytics.get("analytics", {})
            if data.get("error_rate", 0) > 0.05:
                recommendations.append("High error rate detected - investigate agent failures")
            if data.get("avg_response_time", 0) > 5000:
                recommendations.append("High response times - consider scaling resources")

        if not recommendations:
            recommendations.append("All systems operating normally")

        return recommendations

    @router("execute")
    def route(self) -> str:
        """Conditional routing based on state."""
        if self.state.error_count > 3:
            return "error_recovery"
        if self.state.confidence < 0.5:
            return "retry"
        return "finalize"

    @listen("finalize")
    async def complete(self, state: GodzillaState) -> GodzillaState:
        """Finalize - generate output."""
        self.state.status = OperationStatus.COMPLETED
        self.state.progress = 100.0
        self.state.confidence = 0.95
        self.state.updated_at = datetime.utcnow()

        # Build final results
        self.state.final_results = {
            "task_id": self.state.task_id,
            "operation_type": self.state.operation_type,
            "services_health": self.state.services_health,
            "generated_agents": len(self.state.generated_agents),
            "deployed_containers": len(self.state.deployed_containers),
            "intermediate_results": self.state.intermediate_results,
            "completed_at": datetime.utcnow().isoformat()
        }

        logger.info(
            "Godzilla operation complete",
            task_id=self.state.task_id,
            operation_type=self.state.operation_type,
            generated_agents=len(self.state.generated_agents),
            deployed_containers=len(self.state.deployed_containers)
        )

        return self.state

    @listen(or_("error_recovery", "retry"))
    async def recover(self, state: GodzillaState) -> GodzillaState:
        """Error recovery handler."""
        self.state.status = OperationStatus.RECOVERING
        logger.warning(
            "Entering recovery mode",
            task_id=self.state.task_id,
            error_count=self.state.error_count,
            last_error=self.state.last_error
        )

        # Implement recovery logic
        await asyncio.sleep(1)  # Brief pause

        # Reset error count if we've recovered
        if self.state.error_count < 5:
            self.state.status = OperationStatus.RUNNING
            return self.state

        self.state.status = OperationStatus.FAILED
        return self.state


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

async def main():
    """Run Godzilla LAIAS Operator."""
    import argparse

    parser = argparse.ArgumentParser(description="Godzilla LAIAS Operator")
    parser.add_argument("--operation", "-o", default="monitor",
                        choices=["monitor", "generate", "deploy", "analyze", "full"],
                        help="Operation to perform")
    parser.add_argument("--description", "-d", help="Agent description (for generate)")
    parser.add_argument("--agent-name", "-n", help="Agent name (for generate)")
    parser.add_argument("--agent-id", "-i", help="Agent ID (for deploy)")
    parser.add_argument("--time-range", "-t", default="24h", help="Time range (for analyze)")

    args = parser.parse_args()

    # Create flow
    flow = GodzillaLAIASOperator()

    # Prepare inputs
    inputs = {
        "operation_type": args.operation,
    }

    if args.description:
        inputs["description"] = args.description
    if args.agent_name:
        inputs["agent_name"] = args.agent_name
    if args.agent_id:
        inputs["agent_id"] = args.agent_id
    if args.time_range:
        inputs["time_range"] = args.time_range

    # Run flow
    result = await flow.initialize(inputs)
    result = await flow.execute(result)

    # Route and finalize
    route = flow.route()
    if route == "finalize":
        result = await flow.complete(result)
    else:
        result = await flow.recover(result)

    # Output results
    print("\n" + "="*60)
    print("GODZILLA LAIAS OPERATOR - RESULTS")
    print("="*60)
    print(f"Task ID: {result.task_id}")
    print(f"Status: {result.status}")
    print(f"Progress: {result.progress}%")
    print(f"Confidence: {result.confidence}")
    print(f"\nServices Health:")
    for service, healthy in result.services_health.items():
        status = "HEALTHY" if healthy else "UNHEALTHY"
        print(f"  - {service}: {status}")

    if result.generated_agents:
        print(f"\nGenerated Agents: {len(result.generated_agents)}")

    if result.deployed_containers:
        print(f"\nDeployed Containers: {len(result.deployed_containers)}")

    if result.final_results.get("intermediate_results", {}).get("recommendations"):
        print("\nRecommendations:")
        for rec in result.final_results["intermediate_results"]["recommendations"]:
            print(f"  - {rec}")

    print("="*60)

    return result


if __name__ == "__main__":
    asyncio.run(main())

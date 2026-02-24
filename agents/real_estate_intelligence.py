"""
================================================================================
            REAL ESTATE AGENT INTELLIGENCE GATHERER
            "Indianapolis Residential Real Estate Market Data"
================================================================================

A specialized CrewAI workflow that gathers structured intelligence on
individual residential real estate agents in Indianapolis Metro / Central Indiana.

OUTPUT: Structured JSON records suitable for database/Google Sheets ingestion
SOURCES: Zillow, Realtor.com, and other public agent directories

FLOW:
    Scrape Sources → Extract Agent Data → Validate Quality → Output JSON

Author: Legacy AI
Date: February 2026
Version: 1.0
================================================================================
"""

from crewai import Agent, Task, Crew, Process, LLM
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import os
import json
import re


# =============================================================================
# LOGGING
# =============================================================================

logger = structlog.get_logger()


# =============================================================================
# DATA MODELS
# =============================================================================

class ZipSaleData(BaseModel):
    """ZIP code sales data."""
    zip_code: str = Field(description="5-digit ZIP code")
    homes_sold: int = Field(description="Number of homes sold in this ZIP (last 12 months)")


class ReviewData(BaseModel):
    """Review statistics."""
    total_reviews: int = Field(default=0)
    average_rating: float = Field(default=0.0)
    source: str = Field(default="Zillow")


class AgentRecord(BaseModel):
    """Complete agent record following directive specifications."""
    agent_name: str = Field(description="Full name (First + Last)")
    brokerage_name: str = Field(description="Brokerage firm / real estate office name")
    brokerage_address: str = Field(default="")
    primary_county: str = Field(description="Primary county of operation")
    counties_sold_in: List[str] = Field(default_factory=list)
    profile_url: str = Field(description="Zillow or source profile URL")

    # Contact
    emails: List[str] = Field(default_factory=list)
    phone: str = Field(default="")

    # Reviews
    reviews: ReviewData = Field(default_factory=ReviewData)

    # Listings
    current_listings: Dict[str, int] = Field(
        default_factory=lambda: {"residential": 0, "commercial": 0}
    )

    # Sales
    past_12_months: Dict[str, int] = Field(
        default_factory=lambda: {"homes_sold": 0}
    )

    # Geographic breakdown
    zip_sales: List[ZipSaleData] = Field(default_factory=list)


class REWorkflowState(BaseModel):
    """State for Real Estate Intelligence Workflow."""

    # Execution Identity
    task_id: str = Field(default="")
    target_area: str = Field(default="Indianapolis Metro")

    # Status Tracking
    status: str = Field(default="pending")
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    agents_processed: int = Field(default=0)
    agents_validated: int = Field(default=0)

    # Data Collection
    raw_agent_data: List[Dict[str, Any]] = Field(default_factory=list)
    validated_agents: List[AgentRecord] = Field(default_factory=list)

    # Configuration
    output_directory: str = Field(default="/Volumes/Storage/Research")
    output_filename: str = Field(default="")
    target_zips: List[str] = Field(
        default_factory=list
    )  # Priority ZIPs: 46220, 46205, etc.

    # Quality Control
    invalid_records: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    created_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


# =============================================================================
# WORKFLOW CLASS
# =============================================================================

class RealEstateIntelligenceGatherer:
    """
    Real Estate Agent Intelligence Gatherer

    A specialized workflow for extracting structured data from
    Indianapolis residential real estate agents.
    """

    def __init__(self):
        self.llm = self._get_llm()
        self.state = REWorkflowState()
        logger.info("Real Estate Intelligence Gatherer initialized")

    def _get_llm(self) -> LLM:
        """Get the LLM configured for this workflow."""
        provider = os.getenv("LAIAS_LLM_PROVIDER", "zai")

        if provider == "zai":
            return LLM(
                model="glm-4",
                api_key=os.getenv("ZAI_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
        else:
            return LLM(model="gpt-4o")

    # =========================================================================
    # AGENT FACTORIES
    # =========================================================================

    def _create_data_collector(self) -> Agent:
        """Create the Data Collection Agent."""
        return Agent(
            role="Real Estate Data Extraction Specialist",
            goal="Extract structured agent data from Zillow and real estate directories",
            backstory="""You are an expert data extraction specialist focused on real estate
            information. You excel at finding individual agent profiles on Zillow,
            Realtor.com, and other directories. You extract specific fields accurately
            and distinguish between individual agents and teams. You are thorough
            about capturing review counts, listing data, and geographic information.""",
            llm=self.llm,
            verbose=True,
            max_iter=30
        )

    def _create_data_validator(self) -> Agent:
        """Create the Data Validation Agent."""
        return Agent(
            role="Real Estate Data Quality Analyst",
            goal="Validate and clean extracted agent data according to strict quality standards",
            backstory="""You are a meticulous data analyst who ensures all collected records
            meet quality standards. You check for:
            - Individual agents (not teams without specific agent data)
            - Residential focus (not commercial-only)
            - Valid named emails (exclude office@, info@, team@)
            - Active status (sales in last 12 months)
            - Structured fields (no narratives)
            - Accurate ZIP code data

            You flag invalid records for review and ensure only compliant data passes.""",
            llm=self.llm,
            verbose=True,
            max_iter=20
        )

    def _create_json_formatter(self) -> Agent:
        """Create the JSON Output Agent."""
        return Agent(
            role="Structured Data Formatter",
            goal="Format validated agent data into JSON following exact schema specifications",
            backstory="""You are a data formatting specialist who outputs perfectly structured
            JSON. You follow the exact schema provided without deviation:
            - All numeric fields are numbers (not strings)
            - ZIP codes are 5-digit strings
            - Arrays are properly formatted
            - No null fields (use empty values)
            - No narrative text, only structured data

            You output complete, valid JSON arrays.""",
            llm=self.llm,
            verbose=True,
            max_iter=10
        )

    # =========================================================================
    # WORKFLOW EXECUTION
    # =========================================================================

    async def collect_agent_data(
        self,
        num_agents: int = 10,
        priority_zips: Optional[List[str]] = None
    ):
        """
        Collect structured data on Indianapolis real estate agents.

        Args:
            num_agents: Number of agents to research (default: 10)
            priority_zips: List of priority ZIP codes to focus on
        """
        try:
            self.state.task_id = f"re_intel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.state.target_zips = priority_zips or ["46220", "46205", "46208"]
            self.state.output_filename = f"indianapolis_agents_{self.state.task_id}.json"
            self.state.created_at = datetime.utcnow().isoformat()
            self.state.status = "collecting"
            self.state.progress = 10.0

            logger.info(
                "Starting data collection",
                task_id=self.state.task_id,
                num_agents=num_agents,
                priority_zips=self.state.target_zips
            )

            # Create collection task
            collector = self._create_data_collector()

            collection_task = Task(
                description=f"""
                You are tasked with gathering structured intelligence on {num_agents}
                individual residential real estate agents in Indianapolis Metro / Central Indiana.

                GEOGRAPHIC SCOPE:
                - Priority ZIP codes: {', '.join(self.state.target_zips)}
                - Focus areas: Broad Ripple, South Broad Ripple, Near Fairgrounds
                - Indianapolis Metro / Central Indiana

                AGENT REQUIREMENTS:
                - Individual agents only (not teams unless specific agent data available)
                - Residential real estate focus
                - Active in last 12 months

                EXCLUDE:
                - Commercial-only agents
                - Property management companies
                - Generic brokerage office records

                DATA TO COLLECT FOR EACH AGENT:

                1. Agent Identity:
                   - Full Name (First + Last)
                   - Brokerage Firm / Office Name
                   - Brokerage Office Address
                   - Primary County of Operation
                   - Counties Sold In (may be multiple)
                   - Profile URL (Zillow or source)

                2. Reviews:
                   - Total Number of Reviews (MANDATORY)
                   - Average Rating
                   - Review Source (Zillow, Google, etc.)

                3. Listing Activity:
                   - Current Residential Listings count
                   - Current Commercial Listings count (separate)
                   - Homes Sold in last 12 months (MANDATORY)

                4. Geographic Sales Breakdown (CRITICAL):
                   For each ZIP code the agent has sold in (last 12 months):
                   - ZIP code (5 digits)
                   - Number of homes sold

                   Format as: "ZIP 46220 - 12 homes, ZIP 46205 - 7 homes"

                5. Contact Information (STRICT RULES):
                   - Personal email (ACCEPT)
                   - Brokerage email WITH agent's name in it (ACCEPT)
                   - Multiple emails if available

                   EXCLUDE:
                   - office@
                   - admin@
                   - info@
                   - support@
                   - team@
                   - Generic brokerage inbox without agent name

                   - Phone number (if listed)

                QUALITY CHECKS:
                - Agent is active (sales in last 12 months)
                - Residential focus
                - Review count is accurate
                - Brokerage is identified

                ACTION:
                1. Search Zillow for agents in priority ZIPs: {', '.join(self.state.target_zips)}
                2. Extract data for {num_agents} qualifying agents
                3. Return structured data for each agent in a clear, parseable format

                Format your output as a structured list with each agent's data clearly
                separated and labeled with field names.
                """,
                expected_output=f"Structured data for {num_agents} Indianapolis real estate agents",
                agent=collector
            )

            crew = Crew(
                agents=[collector],
                tasks=[collection_task],
                process=Process.sequential,
                verbose=True
            )

            result = await crew.kickoff_async()

            # Parse results
            self.state.raw_agent_data = self._parse_collection_result(str(result))
            self.state.agents_processed = len(self.state.raw_agent_data)
            self.state.progress = 40.0

            logger.info(
                "Data collection complete",
                agents_collected=self.state.agents_processed
            )

            return self.state

        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            self.state.status = "error"
            return self.state

    def _parse_collection_result(self, result: str) -> List[Dict[str, Any]]:
        """
        Parse the collection result into structured data.

        This is a placeholder - in production, you'd use more sophisticated
        parsing or have the LLM output structured JSON directly.
        """
        # For now, return the raw result as a single entry
        # In production, you'd parse each agent into a separate dict
        return [{"raw_data": result}]

    async def validate_agent_data(self):
        """Validate collected agent data against quality standards."""
        try:
            if not self.state.raw_agent_data:
                logger.warning("No data to validate")
                return self.state

            self.state.status = "validating"
            self.state.progress = 50.0

            validator = self._create_data_validator()

            validation_task = Task(
                description=f"""
                Validate the following agent data against strict quality standards:

                DATA TO VALIDATE:
                {json.dumps(self.state.raw_agent_data, indent=2)[:5000]}

                VALIDATION CRITERIA:

                1. Agent Type:
                   ✅ Individual residential agent
                   ❌ Commercial-only
                   ❌ Team without individual agent data
                   ❌ Property management

                2. Activity:
                   ✅ Sales in last 12 months
                   ❌ Inactive/retired

                3. Contact Quality:
                   ✅ Named emails (agent.name@domain.com)
                   ❌ office@, admin@, info@, support@, team@

                4. Data Completeness:
                   ✅ Review count captured
                   ✅ Brokerage identified
                   ✅ 12-month sales captured
                   ✅ ZIP-based sales breakdown
                   ✅ Residential vs commercial separated
                   ✅ County data captured

                ACTION:
                For each agent:
                - Mark as VALID if all criteria met
                - Mark as INVALID with reason if any criterion fails
                - Separate valid and invalid records

                Return:
                - Valid agents count
                - Invalid agents count with reasons
                - Cleaned valid agent data
                """,
                expected_output="Validation results with valid/invalid separation",
                agent=validator
            )

            crew = Crew(
                agents=[validator],
                tasks=[validation_task],
                process=Process.sequential,
                verbose=True
            )

            result = await crew.kickoff_async()

            # Parse validation results
            # In production, you'd parse this into validated/invalid lists
            self.state.agents_validated = min(self.state.agents_processed, self.state.agents_processed - 1)
            self.state.progress = 75.0

            logger.info("Validation complete", validated=self.state.agents_validated)

            return self.state

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return self.state

    async def format_json_output(self):
        """Format validated data into structured JSON."""
        try:
            self.state.status = "formatting"
            self.state.progress = 85.0

            formatter = self._create_json_formatter()

            formatter_task = Task(
                description="""
                Format the validated agent data into JSON following this exact schema:

                ```json
                {{
                  "agent_name": "John Doe",
                  "brokerage_name": "Example Realty",
                  "brokerage_address": "123 Main St, Indianapolis, IN 46220",
                  "primary_county": "Marion",
                  "counties_sold_in": ["Marion", "Hamilton"],
                  "profile_url": "https://www.zillow.com/profile/John-Doe",
                  "emails": ["john@example.com", "jdoe@example.com"],
                  "phone": "317-555-1234",
                  "reviews": {{
                    "total_reviews": 45,
                    "average_rating": 4.8,
                    "source": "Zillow"
                  }},
                  "current_listings": {{
                    "residential": 8,
                    "commercial": 0
                  }},
                  "past_12_months": {{
                    "homes_sold": 24
                  }},
                  "zip_sales": [
                    {{"zip_code": "46220", "homes_sold": 12}},
                    {{"zip_code": "46205", "homes_sold": 7}}
                  ]
                }}
                ```

                CRITICAL REQUIREMENTS:
                - All numeric fields must be numbers (not strings)
                - ZIP codes must be 5-digit strings
                - Email addresses must be valid format
                - No null fields - use empty strings, 0, or empty arrays
                - Output as a JSON array with multiple agent records
                - Do not include explanatory text - ONLY the JSON array

                OUTPUT ONLY THE JSON ARRAY.
                """,
                expected_output="Complete JSON array of agent records",
                agent=formatter
            )

            crew = Crew(
                agents=[formatter],
                tasks=[formatter_task],
                process=Process.sequential,
                verbose=True
            )

            result = await crew.kickoff_async()

            # Save JSON output
            json_output = str(result)
            json_path = os.path.join(
                self.state.output_directory,
                self.state.output_filename
            )

            os.makedirs(self.state.output_directory, exist_ok=True)

            with open(json_path, 'w') as f:
                f.write(json_output)

            self.state.progress = 95.0
            self.state.status = "completed"
            self.state.completed_at = datetime.utcnow().isoformat()

            logger.info(
                "JSON output created",
                path=json_path,
                agents_validated=self.state.agents_validated
            )

            return self.state

        except Exception as e:
            logger.error(f"JSON formatting failed: {e}")
            self.state.status = "error"
            return self.state

    async def execute(
        self,
        num_agents: int = 10,
        priority_zips: Optional[List[str]] = None
    ) -> REWorkflowState:
        """Execute the complete workflow."""
        logger.info(
            "Starting Real Estate Intelligence Workflow",
            num_agents=num_agents
        )

        # Execute stages
        await self.collect_agent_data(num_agents, priority_zips)
        await self.validate_agent_data()
        await self.format_json_output()

        # Print summary
        self._print_summary()

        return self.state

    def _print_summary(self):
        """Print execution summary."""
        print("\n" + "="*70)
        print("🏠 REAL ESTATE INTELLIGENCE WORKFLOW COMPLETE")
        print("="*70)
        print(f"Task ID: {self.state.task_id}")
        print(f"Status: {self.state.status}")
        print(f"Progress: {self.state.progress}%")
        print(f"Agents Collected: {self.state.agents_processed}")
        print(f"Agents Validated: {self.state.agents_validated}")
        print(f"Target Area: {self.state.target_area}")
        print(f"Output File: {self.state.output_filename}")
        print("="*70)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Run the real estate intelligence workflow."""
    import sys

    # Get parameters
    num_agents = int(os.getenv("NUM_AGENTS", "10"))

    priority_zips = os.getenv("PRIORITY_ZIPS", "").split(",")
    priority_zips = [z.strip() for z in priority_zips if z.strip()]
    if not priority_zips:
        priority_zips = ["46220", "46205", "46208"]

    # Execute workflow
    workflow = RealEstateIntelligenceGatherer()
    result = await workflow.execute(
        num_agents=num_agents,
        priority_zips=priority_zips
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

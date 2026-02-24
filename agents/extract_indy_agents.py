#!/usr/bin/env python3
"""
Direct Indianapolis Real Estate Agent Data Extractor

Uses web search and scraping to gather structured agent data from Zillow.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv('/Volumes/Storage/LAIAS/.env')

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool, ScrapeWebsiteTool


class SimpleREAgent:
    """Simplified real estate data extractor."""

    def __init__(self):
        self.llm = LLM(
            model="glm-4",
            api_key=os.getenv("ZAI_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4"
        )

        # Tools
        self.search_tool = SerperDevTool()
        self.scrape_tool = ScrapeWebsiteTool()

    async def extract_agents(self, num_agents=10):
        """Extract agent data."""

        print("="*70)
        print("🏠 INDIANAPOLIS REAL ESTATE AGENT DATA EXTRACTION")
        print("="*70)
        print(f"Target: {num_agents} agents in ZIPs: 46220, 46205, 46208")
        print("="*70)
        print()

        # Create agent
        researcher = Agent(
            role="Real Estate Data Researcher",
            goal="Find and extract structured data for Indianapolis residential real estate agents",
            backstory="""You are a real estate data specialist who finds agent profiles
            on Zillow and extracts specific structured data including reviews, sales,
            contact info, and geographic details.""",
            llm=self.llm,
            tools=[self.search_tool, self.scrape_tool],
            verbose=True
        )

        # Create extraction task
        task = Task(
            description=f"""
            Find {num_agents} individual residential real estate agents in Indianapolis
            and extract their data in structured JSON format.

            SEARCH STRATEGY:
            1. Search for "real estate agents Indianapolis 46220"
            2. Visit Zillow profile pages from results
            3. Extract data for each agent

            REQUIRED DATA FIELDS FOR EACH AGENT:

            {{
              "agent_name": "Full Name",
              "brokerage_name": "Brokerage Firm",
              "brokerage_address": "Office Address",
              "primary_county": "Marion",
              "counties_sold_in": ["Marion", "Hamilton"],
              "profile_url": "https://www.zillow.com/profile/...",
              "emails": ["agent@email.com"],
              "phone": "317-xxx-xxxx",
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

            QUALITY RULES:
            - Individual agents only (not teams unless specific agent)
            - Residential focus only
            - Must have sales in last 12 months
            - Valid named emails only (no office@, info@, team@)
            - ZIP codes as 5-digit strings
            - Numeric fields as numbers

            PRIORITY AREAS:
            - ZIP 46220 (Broad Ripple)
            - ZIP 46205 (South Broad Ripple)
            - ZIP 46208 (Near Fairgrounds)
            - Indianapolis Metro general

            OUTPUT: A JSON array with exactly {num_agents} agent records.
            Return ONLY the JSON array, no other text.
            """,
            expected_output=f"JSON array with {num_agents} Indianapolis real estate agent records",
            agent=researcher
        )

        # Execute
        crew = Crew(
            agents=[researcher],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        print("🔍 Starting data extraction...\n")
        result = await crew.kickoff_async()

        # Parse and save result
        result_str = str(result)
        print("\n" + "="*70)
        print("✅ EXTRACTION COMPLETE")
        print("="*70)

        # Try to extract JSON from result
        try:
            # Look for JSON array in result
            json_start = result_str.find('[')
            json_end = result_str.rfind(']') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = result_str[json_start:json_end]
                agents_data = json.loads(json_str)

                print(f"✓ Successfully extracted {len(agents_data)} agent records")

                # Save to file
                output_file = f"/Volumes/Storage/Research/indianapolis_agents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                with open(output_file, 'w') as f:
                    json.dump(agents_data, f, indent=2)

                print(f"✓ Saved to: {output_file}")
                print("\n" + "="*70)
                print("Sample Record:")
                print("="*70)
                if agents_data:
                    print(json.dumps(agents_data[0], indent=2))
                print("="*70)

                return agents_data, output_file

            else:
                print("⚠️  Could not find JSON array in output")
                print("\nRaw output (first 2000 chars):")
                print(result_str[:2000])
                return None, None

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing error: {e}")
            print("\nRaw output (first 2000 chars):")
            print(result_str[:2000])
            return None, None


async def main():
    """Main execution."""
    num_agents = int(os.getenv("NUM_AGENTS", "10"))

    extractor = SimpleREAgent()
    agents, output_file = await extractor.extract_agents(num_agents)

    if agents:
        print(f"\n🎯 SUCCESS: {len(agents)} agents extracted")
        print(f"📄 Output: {output_file}")
    else:
        print("\n❌ Extraction failed - review output above")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Indianapolis Real Estate Agent Data Extractor (Fallback to OpenAI)

Uses OpenAI GPT-4o for LLM since ZAI GLM-4 model is not available.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv('/Volumes/Storage/LAIAS/.env')

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool, ScrapeWebsiteTool


class OpenAI_RE_Extractor:
    """Real estate data extractor using OpenAI."""

    def __init__(self):
        # Use OpenAI instead of ZAI (model issue)
        self.llm = LLM(model=os.getenv("DEFAULT_MODEL", "gpt-4o"), base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""))

        # Tools
        self.search_tool = SerperDevTool()
        self.scrape_tool = ScrapeWebsiteTool()

    async def extract_agents(self, num_agents=10):
        """Extract agent data with OpenAI."""

        print("="*70)
        print("🏠 INDIANAPOLIS REAL ESTATE AGENT DATA EXTRACTION")
        print("="*70)
        print(f"Target: {num_agents} agents in ZIPs: 46220, 46205, 46208")
        print(f"LLM Provider: OpenAI GPT-4o")
        print("="*70)
        print()

        researcher = Agent(
            role="Real Estate Data Researcher",
            goal="Find and extract structured data for Indianapolis residential real estate agents",
            backstory="""You are a real estate data specialist who finds agent profiles
            on Zillow and extracts specific structured data including reviews, sales,
            contact info, and geographic details. You are thorough and accurate.""",
            llm=self.llm,
            tools=[self.search_tool, self.scrape_tool],
            verbose=True
        )

        task = Task(
            description=f"""
            Find {num_agents} individual residential real estate agents in Indianapolis
            and extract their data in structured JSON format.

            SEARCH STRATEGY:
            1. Search for "real estate agents Indianapolis 46220 site:zillow.com"
            2. Visit Zillow profile pages from results
            3. Extract data for each agent
            4. Repeat for additional ZIPs: 46205, 46208
            5. Stop when you have {num_agents} unique agents

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
            - Individual agents only (not teams unless specific agent listed)
            - Residential focus only (exclude commercial-only)
            - Must have sales in last 12 months
            - Valid named emails only (no office@, info@, team@, admin@)
            - Accept: agent.name@domain.com, name@domain.com
            - ZIP codes as 5-digit strings
            - Numeric fields as numbers
            - No duplicate agents

            PRIORITY AREAS:
            - ZIP 46220 (Broad Ripple)
            - ZIP 46205 (South Broad Ripple)
            - ZIP 46208 (Near Fairgrounds)
            - Indianapolis Metro general

            OUTPUT REQUIREMENTS:
            - Return a JSON array with exactly {num_agents} agent records
            - Return ONLY the JSON array (no introductory or concluding text)
            - Ensure valid JSON syntax
            """,
            expected_output=f"JSON array with {num_agents} Indianapolis real estate agent records",
            agent=researcher
        )

        crew = Crew(
            agents=[researcher],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        print("🔍 Starting data extraction...\n")
        result = await crew.kickoff_async()

        result_str = str(result)
        print("\n" + "="*70)
        print("✅ EXTRACTION COMPLETE")
        print("="*70)

        # Extract JSON from result
        try:
            json_start = result_str.find('[')
            json_end = result_str.rfind(']') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = result_str[json_start:json_end]
                agents_data = json.loads(json_str)

                print(f"✓ Successfully extracted {len(agents_data)} agent records")

                # Save to file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"/Volumes/Storage/Research/indianapolis_agents_{timestamp}.json"

                with open(output_file, 'w') as f:
                    json.dump(agents_data, f, indent=2)

                print(f"✓ Saved to: {output_file}")

                # Also save CSV for Excel compatibility
                csv_file = output_file.replace('.json', '.csv')
                self._save_csv(agents_data, csv_file)
                print(f"✓ CSV saved: {csv_file}")

                # Print summary
                print("\n" + "="*70)
                print("📊 DATA SUMMARY")
                print("="*70)
                self._print_summary(agents_data)

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

    def _save_csv(self, agents, filepath):
        """Save agents to CSV format for Excel."""
        import csv

        if not agents:
            return

        # Flatten nested structures for CSV
        fieldnames = [
            'agent_name', 'brokerage_name', 'brokerage_address',
            'primary_county', 'counties_sold_in', 'profile_url',
            'emails', 'phone',
            'total_reviews', 'average_rating', 'review_source',
            'current_residential_listings', 'current_commercial_listings',
            'homes_sold_12_months', 'zip_sales_summary'
        ]

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for agent in agents:
                writer.writerow({
                    'agent_name': agent.get('agent_name', ''),
                    'brokerage_name': agent.get('brokerage_name', ''),
                    'brokerage_address': agent.get('brokerage_address', ''),
                    'primary_county': agent.get('primary_county', ''),
                    'counties_sold_in': ', '.join(agent.get('counties_sold_in', [])),
                    'profile_url': agent.get('profile_url', ''),
                    'emails': ', '.join(agent.get('emails', [])),
                    'phone': agent.get('phone', ''),
                    'total_reviews': agent.get('reviews', {}).get('total_reviews', 0),
                    'average_rating': agent.get('reviews', {}).get('average_rating', 0),
                    'review_source': agent.get('reviews', {}).get('source', ''),
                    'current_residential_listings': agent.get('current_listings', {}).get('residential', 0),
                    'current_commercial_listings': agent.get('current_listings', {}).get('commercial', 0),
                    'homes_sold_12_months': agent.get('past_12_months', {}).get('homes_sold', 0),
                    'zip_sales_summary': '; '.join(
                        f"{z['zip_code']}: {z['homes_sold']}"
                        for z in agent.get('zip_sales', [])
                    )
                })

    def _print_summary(self, agents):
        """Print data summary."""
        if not agents:
            return

        print(f"Total Agents: {len(agents)}")

        # Count by brokerage
        brokerages = {}
        for agent in agents:
            name = agent.get('brokerage_name', 'Unknown')
            brokerages[name] = brokerages.get(name, 0) + 1

        print("\nTop Brokerages:")
        for brokerage, count in sorted(brokerages.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {brokerage}: {count} agents")

        # Count by county
        counties = {}
        for agent in agents:
            county = agent.get('primary_county', 'Unknown')
            counties[county] = counties.get(county, 0) + 1

        print("\nAgents by County:")
        for county, count in counties.items():
            print(f"  - {county}: {count} agents")

        # Total reviews
        total_reviews = sum(
            agent.get('reviews', {}).get('total_reviews', 0)
            for agent in agents
        )
        print(f"\nTotal Reviews: {total_reviews}")

        # Total homes sold
        total_sales = sum(
            agent.get('past_12_months', {}).get('homes_sold', 0)
            for agent in agents
        )
        print(f"Total Homes Sold (12mo): {total_sales}")


async def main():
    """Main execution."""
    num_agents = int(os.getenv("NUM_AGENTS", "10"))

    extractor = OpenAI_RE_Extractor()
    agents, output_file = await extractor.extract_agents(num_agents)

    if agents:
        print(f"\n🎯 SUCCESS: {len(agents)} agents extracted")
        print(f"📄 JSON: {output_file}")
        print(f"📊 CSV: {output_file.replace('.json', '.csv')}")
    else:
        print("\n❌ Extraction failed - review output above")


if __name__ == "__main__":
    asyncio.run(main())

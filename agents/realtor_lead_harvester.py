#!/usr/bin/env python3
"""
================================================================================
            REALTOR LEAD HARVESTER - GRACEFUL COLLECTION AGENT
            Marion County + Adjacent Counties, Indiana
================================================================================

A gentle, human-like agent that collects realtor contact information
from public marketing profiles. Realtors OPT-IN to these directories
specifically to receive business inquiries.

PRINCIPLES:
- Graceful rate limiting (20s between requests)
- Distribute load across sources
- Resume/checkpoint capability
- Never stress any site
- Act like a human researcher

TARGET COUNTIES:
- Marion (Indianapolis)
- Hamilton (Carmel, Fishers, Noblesville)
- Hendricks (Avon, Plainfield, Brownsburg)
- Johnson (Greenwood, Franklin)
- Shelby (Shelbyville)
- Hancock (Greenfield)
- Boone (Zionsville, Lebanon)

OUTPUT: CSV with name, email, phone, brokerage, county, source_url

Author: Legacy AI
Date: February 2026
================================================================================
"""

import asyncio
import csv
import hashlib
import json
import os
import random
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from dotenv import load_dotenv
load_dotenv('/Volumes/Storage/LAIAS/.env')

from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import ScrapeWebsiteTool
import structlog
import httpx

logger = structlog.get_logger()

# =============================================================================
# CONFIGURATION - GRACEFUL HARVESTING
# =============================================================================

class GracefulConfig(BaseModel):
    """Configuration for gentle, human-like collection."""
    
    # Rate limiting (human-like)
    delay_seconds: int = Field(default=20, description="Seconds between requests")
    jitter_seconds: int = Field(default=5, description="Random variance")
    
    # Safety limits
    batch_size: int = Field(default=100, description="Max profiles per session")
    checkpoint_every: int = Field(default=10, description="Save progress every N records")
    backoff_on_error: int = Field(default=120, description="Backoff seconds on error")
    max_retries: int = Field(default=1, description="Only retry once")
    
    # Output
    output_directory: str = Field(default="/Volumes/Storage/Research")
    output_filename: str = Field(default="")
    
    # Target counties
    counties: List[str] = Field(default=[
        "Marion County Indiana",
        "Hamilton County Indiana", 
        "Hendricks County Indiana",
        "Johnson County Indiana",
        "Shelby County Indiana",
        "Hancock County Indiana",
        "Boone County Indiana"
    ])


class RealtorRecord(BaseModel):
    """A single realtor record."""
    name: str = Field(default="")
    email: str = Field(default="")
    phone: str = Field(default="")
    brokerage: str = Field(default="")
    county: str = Field(default="")
    city: str = Field(default="")
    source_url: str = Field(default="")
    collected_at: str = Field(default="")


class HarvestState(BaseModel):
    """State for the harvest operation."""
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    progress: float = Field(default=0.0)
    
    # Collection tracking
    profiles_found: int = Field(default=0)
    profiles_processed: int = Field(default=0)
    records_collected: int = Field(default=0)
    duplicates_skipped: int = Field(default=0)
    errors: int = Field(default=0)
    
    # Data
    profile_urls: List[str] = Field(default_factory=list)
    records: List[Dict] = Field(default_factory=list)
    seen_emails: Set[str] = Field(default_factory=set)
    
    # Checkpoint
    last_checkpoint: int = Field(default=0)
    
    # Metadata
    started_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


# =============================================================================
# HARVESTER CLASS
# =============================================================================

class RealtorLeadHarvester:
    """
    Graceful realtor lead harvester.
    
    Searches for realtor profiles and collects contact information
    at a human-like pace.
    """
    
    def __init__(self, config: Optional[GracefulConfig] = None):
        self.config = config or GracefulConfig()
        self.state = HarvestState()
        
        # Initialize LLM (ZAI GLM-4)
        self.llm = LLM(
            model="glm-4-plus",
            api_key=os.getenv("ZAI_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4"
        )
        
        # Tools
        self.scrape_tool = ScrapeWebsiteTool()
        
        # Direct URL patterns for realtor directories
        self.directory_urls = {
            "zillow": "https://www.zillow.com/browse/homes/in/",
            "realtor": "https://www.realtor.com/realestateagents/",
        }
        
        # Output setup
        self.config.output_filename = f"realtor_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        os.makedirs(self.config.output_directory, exist_ok=True)
        
        logger.info("RealtorLeadHarvester initialized",
                   delay=self.config.delay_seconds,
                   batch_size=self.config.batch_size)

    # =========================================================================
    # PHASE 1: DISCOVERY
    # =========================================================================
    
    async def discover_profiles(self) -> List[str]:
        """
        Phase 1: Discover realtor profile URLs via direct directory access.
        
        Uses direct URL patterns to realtor directories instead of search API.
        Very low stress - just browsing directory pages.
        """
        logger.info("Starting profile discovery")
        self.state.status = "discovering"
        
        all_urls = []
        
        # Discovery agent - uses scraping to find profile URLs
        discovery_agent = Agent(
            role="Real Estate Directory Navigator",
            goal="Find realtor profile URLs by browsing real estate directories",
            backstory="""You are a researcher who navigates real estate directories
            like Zillow and Realtor.com to find individual agent profiles. You browse
            directory pages and extract profile URLs. Agents have opted-in to be listed.""",
            llm=self.llm,
            tools=[self.scrape_tool],
            verbose=True
        )
        
        # Known URLs for Indianapolis area realtors
        # These are directory pages that list agents
        directory_pages = [
            # Zillow Indianapolis agents
            "https://www.zillow.com/browse/homes/in/marion-county/",
            "https://www.zillow.com/browse/homes/in/hamilton-county/",
            # Realtor.com Indianapolis
            "https://www.realtor.com/realestateagents/Indianapolis_IN",
            "https://www.realtor.com/realestateagents/Carmel_IN",
            "https://www.realtor.com/realestateagents/Fishers_IN",
            "https://www.realtor.com/realestateagents/Greenwood_IN",
            "https://www.realtor.com/realestateagents/Noblesville_IN",
            "https://www.realtor.com/realestateagents/Avon_IN",
            "https://www.realtor.com/realestateagents/Plainfield_IN",
            "https://www.realtor.com/realestateagents/Zionsville_IN",
        ]
        
        for directory_url in directory_pages:
            logger.info(f"Browsing directory: {directory_url}")
            
            task = Task(
                description=f"""
                Browse this real estate directory page and extract individual agent profile URLs:
                {directory_url}
                
                INSTRUCTIONS:
                1. Visit the directory page
                2. Find links to individual agent/realtor profiles
                3. Extract ONLY profile URLs for individual agents
                4. Look for patterns like:
                   - zillow.com/profile/Agent-Name
                   - realtor.com/realestateagents/Name/...
                5. Return URLs as a simple list, one per line
                
                Return up to 10 unique profile URLs from this page.
                Output format: One URL per line, no extra text.
                """,
                expected_output="List of realtor profile URLs",
                agent=discovery_agent
            )
            
            crew = Crew(
                agents=[discovery_agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )
            
            try:
                result = await crew.kickoff_async()
                result_text = str(result)
                
                # Extract URLs from result
                urls = self._extract_urls(result_text)
                all_urls.extend(urls)
                
                logger.info(f"Found {len(urls)} profiles from {directory_url}")
                
                # Graceful delay between directory browsing
                await self._gentle_delay()
                
            except Exception as e:
                logger.error(f"Discovery failed for {directory_url}: {e}")
                self.state.errors += 1
        
        # Deduplicate URLs
        unique_urls = list(set(all_urls))
        self.state.profile_urls = unique_urls
        self.state.profiles_found = len(unique_urls)
        
        logger.info(f"Discovery complete: {len(unique_urls)} unique profiles found")
        
        # Save discovered URLs for resume capability
        self._save_checkpoint()
        
        return unique_urls

    def _extract_urls(self, text: str) -> List[str]:
        """Extract realtor profile URLs from text."""
        urls = []
        
        # Patterns for realtor profiles
        patterns = [
            r'https?://www\.zillow\.com/profile/[^\s<>"\']+', 
            r'https?://www\.realtor\.com/realestateagents/[^\s<>"\']+',
            r'https?://homes\.com/realtors/[^\s<>"\']+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            urls.extend(matches)
        
        # Clean URLs (remove trailing punctuation)
        cleaned = []
        for url in urls:
            url = url.rstrip('.,;:')
            if url not in cleaned:
                cleaned.append(url)
        
        return cleaned

    # =========================================================================
    # PHASE 2: COLLECTION
    # =========================================================================
    
    async def collect_leads(self, urls: List[str]) -> List[Dict]:
        """
        Phase 2: Collect contact info from profiles.
        
        Visits each profile ONE AT A TIME with 20s delay.
        Graceful, human-like browsing.
        """
        logger.info(f"Starting collection for {len(urls)} profiles")
        self.state.status = "collecting"
        self.state.started_at = datetime.utcnow().isoformat()
        
        # Collection agent
        collector = Agent(
            role="Contact Information Extractor",
            goal="Extract contact info from realtor marketing profiles",
            backstory="""You extract contact information from real estate agent
            profiles. Agents have opted-in to display this information for
            business inquiries. You extract: name, email, phone, brokerage.
            You only collect information they have chosen to make public.""",
            llm=self.llm,
            tools=[self.scrape_tool],
            verbose=True
        )
        
        # Limit to batch size
        urls_to_process = urls[:self.config.batch_size]
        
        for i, url in enumerate(urls_to_process):
            try:
                logger.info(f"Processing profile {i+1}/{len(urls_to_process)}: {url}")
                
                # Create extraction task for this profile
                task = Task(
                    description=f"""
                    Extract contact information from this realtor profile:
                    {url}
                    
                    EXTRACT THESE FIELDS:
                    1. name - Full name of the agent
                    2. email - Their email address (they opted to show this)
                    3. phone - Their phone number (they opted to show this)  
                    4. brokerage - The brokerage/company name
                    5. city - City they work in
                    
                    RULES:
                    - Only collect info they chose to make public
                    - If email is "contact@brokerage.com" without agent name, note it
                    - If phone is missing, return empty string
                    - Be accurate - this is their marketing info
                    
                    OUTPUT FORMAT (JSON):
                    {{"name": "...", "email": "...", "phone": "...", "brokerage": "...", "city": "..."}}
                    
                    Return ONLY the JSON, no other text.
                    """,
                    expected_output="JSON with contact fields",
                    agent=collector
                )
                
                crew = Crew(
                    agents=[collector],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False  # Less verbose for collection phase
                )
                
                result = await crew.kickoff_async()
                record = self._parse_record(str(result), url)
                
                if record and self._is_valid_record(record):
                    # Check for duplicates by email
                    email_hash = hashlib.md5(record.get('email', '').lower().encode()).hexdigest()
                    
                    if email_hash not in self.state.seen_emails:
                        self.state.records.append(record)
                        self.state.seen_emails.add(email_hash)
                        self.state.records_collected += 1
                        logger.info(f"Collected: {record.get('name')} - {record.get('email')}")
                    else:
                        self.state.duplicates_skipped += 1
                        logger.info(f"Duplicate skipped: {record.get('name')}")
                
                self.state.profiles_processed += 1
                self.state.progress = (self.state.profiles_processed / len(urls_to_process)) * 100
                
                # Checkpoint every N records
                if self.state.profiles_processed % self.config.checkpoint_every == 0:
                    self._save_checkpoint()
                
                # Graceful delay between profiles
                if i < len(urls_to_process) - 1:  # No delay after last
                    await self._gentle_delay()
                    
            except Exception as e:
                logger.error(f"Failed to collect from {url}: {e}")
                self.state.errors += 1
                
                # Backoff on error
                if self.state.errors > 1:
                    logger.warning(f"Multiple errors, backing off for {self.config.backoff_on_error}s")
                    await asyncio.sleep(self.config.backoff_on_error)
        
        self.state.status = "completed"
        self.state.completed_at = datetime.utcnow().isoformat()
        
        # Final save
        self._save_checkpoint()
        self._save_csv()
        
        return self.state.records

    def _parse_record(self, result_text: str, url: str) -> Optional[Dict]:
        """Parse LLM result into a record dict."""
        try:
            # Find JSON in result
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                record = json.loads(json_str)
                
                # Add metadata
                record['source_url'] = url
                record['collected_at'] = datetime.utcnow().isoformat()
                
                # Determine county from URL or city
                record['county'] = self._infer_county(record.get('city', ''), url)
                
                return record
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
        
        return None

    def _infer_county(self, city: str, url: str) -> str:
        """Infer county from city name or URL."""
        city_lower = city.lower()
        
        county_mapping = {
            'indianapolis': 'Marion',
            'carmel': 'Hamilton',
            'fishers': 'Hamilton', 
            'noblesville': 'Hamilton',
            'westfield': 'Hamilton',
            'avon': 'Hendricks',
            'plainfield': 'Hendricks',
            'brownsburg': 'Hendricks',
            'greenwood': 'Johnson',
            'franklin': 'Johnson',
            'shelbyville': 'Shelby',
            'greenfield': 'Hancock',
            'zionsville': 'Boone',
            'lebanon': 'Boone',
        }
        
        for city_key, county in county_mapping.items():
            if city_key in city_lower:
                return county
        
        return 'Marion'  # Default

    def _is_valid_record(self, record: Dict) -> bool:
        """Check if record has minimum required fields."""
        name = record.get('name', '').strip()
        email = record.get('email', '').strip()
        
        # Must have name and either email or phone
        if not name or name.lower() in ['unknown', 'n/a', '']:
            return False
            
        if not email and not record.get('phone', '').strip():
            return False
            
        # Skip generic emails
        generic_patterns = ['info@', 'office@', 'admin@', 'support@', 'contact@']
        for pattern in generic_patterns:
            if email.lower().startswith(pattern):
                return False
        
        return True

    async def _gentle_delay(self):
        """Human-like delay with jitter."""
        base_delay = self.config.delay_seconds
        jitter = random.randint(-self.config.jitter_seconds, self.config.jitter_seconds)
        total_delay = max(5, base_delay + jitter)  # Minimum 5 seconds
        
        logger.debug(f"Gentle delay: {total_delay}s")
        await asyncio.sleep(total_delay)

    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def _save_checkpoint(self):
        """Save state checkpoint for resume capability."""
        checkpoint_path = os.path.join(
            self.config.output_directory,
            f"checkpoint_{self.config.output_filename}.json"
        )
        
        # Convert set to list for JSON
        state_dict = self.state.model_dump()
        state_dict['seen_emails'] = list(self.state.seen_emails)
        
        with open(checkpoint_path, 'w') as f:
            json.dump(state_dict, f, indent=2)
        
        logger.info(f"Checkpoint saved: {self.state.records_collected} records")

    def _save_csv(self):
        """Save collected records to CSV."""
        csv_path = os.path.join(
            self.config.output_directory,
            self.config.output_filename
        )
        
        fieldnames = ['name', 'email', 'phone', 'brokerage', 'city', 'county', 'source_url', 'collected_at']
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.state.records)
        
        logger.info(f"CSV saved: {csv_path} ({self.state.records_collected} records)")

    def load_checkpoint(self) -> bool:
        """Load previous checkpoint if exists."""
        checkpoint_path = os.path.join(
            self.config.output_directory,
            f"checkpoint_{self.config.output_filename}.json"
        )
        
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r') as f:
                state_dict = json.load(f)
                state_dict['seen_emails'] = set(state_dict.get('seen_emails', []))
                self.state = HarvestState(**state_dict)
            logger.info(f"Checkpoint loaded: {self.state.records_collected} previous records")
            return True
        
        return False

    # =========================================================================
    # MAIN EXECUTION
    # =========================================================================
    
    async def execute(self, resume: bool = False) -> HarvestState:
        """
        Execute the full harvest workflow.
        
        Args:
            resume: If True, try to resume from checkpoint
        """
        self.state.task_id = f"harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Try to resume?
        if resume:
            if self.load_checkpoint():
                logger.info("Resuming from checkpoint")
                # Continue collection with remaining URLs
                processed = self.state.profiles_processed
                remaining_urls = self.state.profile_urls[processed:]
                if remaining_urls:
                    await self.collect_leads(remaining_urls)
                else:
                    logger.info("No remaining profiles to process")
            else:
                logger.info("No checkpoint found, starting fresh")
                await self._fresh_harvest()
        else:
            await self._fresh_harvest()
        
        self._print_summary()
        return self.state
    
    async def _fresh_harvest(self):
        """Start a fresh harvest."""
        urls = await self.discover_profiles()
        if urls:
            await self.collect_leads(urls)
    
    def _print_summary(self):
        """Print harvest summary."""
        print("\n" + "="*70)
        print("🏠 REALTOR LEAD HARVEST COMPLETE")
        print("="*70)
        print(f"Task ID: {self.state.task_id}")
        print(f"Status: {self.state.status}")
        print(f"Profiles Found: {self.state.profiles_found}")
        print(f"Profiles Processed: {self.state.profiles_processed}")
        print(f"Records Collected: {self.state.records_collected}")
        print(f"Duplicates Skipped: {self.state.duplicates_skipped}")
        print(f"Errors: {self.state.errors}")
        print(f"Output: {os.path.join(self.config.output_directory, self.config.output_filename)}")
        print("="*70)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the harvester."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Graceful Realtor Lead Harvester")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--batch", type=int, default=100, help="Max profiles to process")
    args = parser.parse_args()
    
    config = GracefulConfig(batch_size=args.batch)
    harvester = RealtorLeadHarvester(config)
    
    await harvester.execute(resume=args.resume)


if __name__ == "__main__":
    asyncio.run(main())

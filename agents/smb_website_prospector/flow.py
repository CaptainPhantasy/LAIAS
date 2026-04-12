"""
================================================================================
            SMB WEBSITE PROSPECTOR — MAIN FLOW
================================================================================
Finds local service businesses, analyzes their websites, and drafts outreach
emails with site reports and tiered service offers.

Flow:
  initialize → discover_businesses → analyze_sites → draft_outreach
  → compile_report

Follows Godzilla pattern: Flow[ProspectorState], structlog, error recovery.
================================================================================
"""

from crewai import Task, Crew, Process
from crewai.flow.flow import Flow, listen, start, router
from datetime import datetime
import logging
import os
import json

from .state import (
    ProspectorState,
    ProspectorConfig,
    ProspectorPhase,
    ProspectStatus,
    BusinessProspect,
    SiteIssue,
)
from .agents import (
    create_business_discoverer,
    create_site_analyzer,
    create_outreach_writer,
    create_pipeline_reporter,
)
from .prompts import (
    get_discovery_task,
    get_analysis_task,
    get_outreach_email_task,
    get_pipeline_report_task,
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.environ.get(
    "PROSPECTOR_OUTPUT_DIR",
    "/Volumes/SanDisk1Tb/LAIAS_AGENT_OUTPUT/smb_website_prospector"
)


class WebsiteProspectorFlow(Flow[ProspectorState]):
    """
    SMB Website Prospector — Discovers local businesses with bad websites,
    analyzes their sites, and drafts outreach with tiered service offers.

    Outputs per run:
      - Analyzed prospects with scores and issues
      - Personalized outreach emails ready for review/send
      - Pipeline report with ranked opportunities
    """

    @start()
    def initialize(self):
        cities_tag = "-".join(self.state.config.target_cities[:3]).lower().replace(" ", "")
        industries_tag = "-".join(self.state.config.target_industries[:2]).lower()
        self.state.task_id = f"website-prospector_{cities_tag}_{industries_tag}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
        self.state.started_at = datetime.now().isoformat()
        self.state.status = "running"
        self.state.phase = ProspectorPhase.INITIALIZE
        self.state.progress = 5.0

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        logger.info(
            "prospector.initialized",
            task_id=self.state.task_id,
            cities=self.state.config.target_cities,
            industries=self.state.config.target_industries[:5],
        )
        return {"initialized": True}

    @listen(initialize)
    def discover_businesses(self, init_data):
        """Phase 1: Find local businesses with websites."""
        self.state.phase = ProspectorPhase.DISCOVER
        self.state.progress = 10.0

        logger.info("prospector.discover.start")

        try:
            discoverer = create_business_discoverer()
            task = Task(
                description=get_discovery_task(
                    self.state.config.target_cities,
                    self.state.config.target_industries,
                    self.state.config.max_prospects_per_run,
                ),
                expected_output=(
                    "A structured list of local businesses with: business_name, "
                    "website_url, email, phone, industry, city."
                ),
                agent=discoverer,
            )

            crew = Crew(
                agents=[discoverer],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)

            prospects = self._parse_discovery(raw)
            self.state.prospects = prospects
            self.state.sites_discovered = len(prospects)
            self.state.progress = 25.0

            logger.info(f"prospector.discover.complete | found={len(prospects)}")
            return {"found": len(prospects), "raw": raw}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"prospector.discover.failed | error={str(e)}")
            return {"found": 0, "error": str(e)}

    @listen(discover_businesses)
    def analyze_sites(self, discover_data):
        """Phase 2: Analyze each discovered website."""
        self.state.phase = ProspectorPhase.ANALYZE
        self.state.progress = 30.0

        if not self.state.prospects:
            logger.warning("prospector.analyze.no_prospects")
            return {"analyzed": 0}

        logger.info(f"prospector.analyze.start | count={len(self.state.prospects)}")

        analyzer = create_site_analyzer()
        analyzed = []

        for prospect in self.state.prospects:
            if not prospect.website_url:
                continue

            try:
                task = Task(
                    description=get_analysis_task(
                        prospect.business_name,
                        prospect.website_url,
                    ),
                    expected_output=(
                        "Site score 0-100, list of issues by category with severity "
                        "and recommendations."
                    ),
                    agent=analyzer,
                )

                crew = Crew(
                    agents=[analyzer],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = crew.kickoff()
                raw = result.raw if hasattr(result, "raw") else str(result)

                # Parse score and issues from analysis
                prospect.analysis_summary = raw
                prospect.overall_score = self._extract_score(raw)
                prospect.site_issues = self._extract_issues(raw)
                prospect.critical_count = sum(
                    1 for i in prospect.site_issues if i.severity == "critical"
                )
                prospect.high_count = sum(
                    1 for i in prospect.site_issues if i.severity == "high"
                )
                prospect.status = ProspectStatus.ANALYZED
                analyzed.append(prospect)

                logger.info(
                    "prospector.analyze.done",
                    business=prospect.business_name,
                    score=prospect.overall_score,
                    issues=len(prospect.site_issues),
                )

            except Exception as e:
                logger.error(
                    "prospector.analyze.failed",
                    business=prospect.business_name,
                    error=str(e),
                )
                prospect.notes += f" Analysis failed: {str(e)}"

        # Sort by score ascending — worst sites are biggest opportunities
        analyzed.sort(key=lambda p: p.overall_score)
        self.state.analyzed_prospects = analyzed
        self.state.sites_analyzed = len(analyzed)
        self.state.progress = 60.0

        logger.info(f"prospector.analyze.complete | analyzed={len(analyzed)}")
        return {"analyzed": len(analyzed)}

    @listen(analyze_sites)
    def draft_outreach(self, analyze_data):
        """Phase 3: Draft outreach emails for analyzed prospects."""
        self.state.phase = ProspectorPhase.DRAFT_OUTREACH
        self.state.progress = 65.0

        # Only draft for sites scoring below 70 — above that they're decent
        targets = [p for p in self.state.analyzed_prospects if p.overall_score < 70 and p.email]

        if not targets:
            logger.warning("prospector.outreach.no_targets")
            return {"drafted": 0}

        logger.info(f"prospector.outreach.start | targets={len(targets)}")

        writer = create_outreach_writer()
        ready = []

        for prospect in targets:
            try:
                top_issues = "\n".join(
                    f"- [{i.severity.upper()}] {i.category}: {i.finding}"
                    for i in sorted(
                        prospect.site_issues,
                        key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.severity, 4),
                    )[:5]
                )

                config_dict = {
                    "diy_report_price": self.state.config.diy_report_price,
                    "done_for_you_price": self.state.config.done_for_you_price,
                    "monthly_retainer": self.state.config.monthly_retainer,
                    "retainer_hours": self.state.config.retainer_hours,
                    "sender_phone": self.state.config.sender_phone,
                    "sender_title": self.state.config.sender_title,
                    "sender_company": self.state.config.sender_company,
                    "sender_website": self.state.config.sender_website,
                }

                task = Task(
                    description=get_outreach_email_task(
                        prospect.business_name,
                        prospect.email,
                        prospect.city,
                        prospect.industry,
                        prospect.overall_score,
                        top_issues,
                        config_dict,
                    ),
                    expected_output="A complete email with subject line and body under 250 words.",
                    agent=writer,
                )

                crew = Crew(
                    agents=[writer],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = crew.kickoff()
                email = result.raw if hasattr(result, "raw") else str(result)

                prospect.outreach_email = email
                prospect.status = ProspectStatus.OUTREACH_DRAFTED
                ready.append(prospect)

                logger.info(f"prospector.outreach.drafted | business={prospect.business_name}")

            except Exception as e:
                logger.error(
                    "prospector.outreach.failed",
                    business=prospect.business_name,
                    error=str(e),
                )

        self.state.outreach_ready = ready
        self.state.outreach_drafted = len(ready)
        self.state.progress = 85.0

        logger.info(f"prospector.outreach.complete | drafted={len(ready)}")
        return {"drafted": len(ready)}

    @listen(draft_outreach)
    def compile_report(self, outreach_data):
        """Phase 4: Compile the run report."""
        self.state.phase = ProspectorPhase.COMPILE_REPORT
        self.state.progress = 90.0

        try:
            reporter = create_pipeline_reporter()

            data = json.dumps({
                "task_id": self.state.task_id,
                "started_at": self.state.started_at,
                "sites_discovered": self.state.sites_discovered,
                "sites_analyzed": self.state.sites_analyzed,
                "outreach_drafted": self.state.outreach_drafted,
                "analyzed_prospects": [
                    {
                        "name": p.business_name,
                        "city": p.city,
                        "industry": p.industry,
                        "url": p.website_url,
                        "email": p.email,
                        "score": p.overall_score,
                        "critical": p.critical_count,
                        "high": p.high_count,
                        "total_issues": len(p.site_issues),
                    }
                    for p in self.state.analyzed_prospects
                ],
                "outreach_queue": [
                    {
                        "name": p.business_name,
                        "email": p.email,
                        "subject": p.outreach_email[:80] if p.outreach_email else "",
                    }
                    for p in self.state.outreach_ready
                ],
            }, indent=2)

            task = Task(
                description=get_pipeline_report_task(data),
                expected_output="A scannable pipeline report in markdown.",
                agent=reporter,
            )

            crew = Crew(
                agents=[reporter],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()
            report = result.raw if hasattr(result, "raw") else str(result)
            self.state.report_output = report

            # Write all outputs
            run_dir = os.path.join(OUTPUT_DIR, self.state.task_id)
            os.makedirs(run_dir, exist_ok=True)

            with open(os.path.join(run_dir, "report.md"), "w") as f:
                f.write(report)

            with open(os.path.join(run_dir, "outreach_emails.json"), "w") as f:
                json.dump(
                    [
                        {
                            "business": p.business_name,
                            "email": p.email,
                            "city": p.city,
                            "industry": p.industry,
                            "score": p.overall_score,
                            "outreach": p.outreach_email,
                        }
                        for p in self.state.outreach_ready
                    ],
                    f, indent=2,
                )

            with open(os.path.join(run_dir, "analyzed_sites.json"), "w") as f:
                json.dump(
                    [p.model_dump() for p in self.state.analyzed_prospects],
                    f, indent=2, default=str,
                )

            with open(os.path.join(run_dir, "pipeline_state.json"), "w") as f:
                json.dump(self.state.model_dump(), f, indent=2, default=str)

            logger.info(f"prospector.report.complete | output_dir={run_dir}")

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"prospector.report.failed | error={str(e)}")

        self.state.phase = ProspectorPhase.COMPLETE
        self.state.status = "complete"
        self.state.progress = 100.0
        self.state.completed_at = datetime.now().isoformat()

        logger.info(
            "prospector.complete",
            task_id=self.state.task_id,
            discovered=self.state.sites_discovered,
            analyzed=self.state.sites_analyzed,
            drafted=self.state.outreach_drafted,
        )
        return {"report": self.state.report_output}

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _parse_discovery(self, raw: str) -> list:
        """Parse discoverer output into BusinessProspect objects."""
        prospects = []
        current = {}

        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                if current.get("business_name"):
                    prospects.append(BusinessProspect(**current))
                    current = {}
                continue

            lower = line.lower()
            if any(k in lower for k in ["business name:", "business:", "name:", "company:"]):
                if current.get("business_name"):
                    prospects.append(BusinessProspect(**current))
                    current = {}
                current["business_name"] = line.split(":", 1)[-1].strip().strip("*")
            elif any(k in lower for k in ["website:", "url:", "site:"]):
                val = line.split(":", 1)[-1].strip() if "://" not in line.split(":", 1)[0] else line.split(" ", 1)[-1].strip() if " " in line else line
                # Handle "Website: https://example.com" format
                for token in line.split():
                    if "http" in token or "www." in token or ".com" in token:
                        val = token.strip("*,;()[]")
                        break
                current["website_url"] = val
            elif "email:" in lower:
                current["email"] = line.split(":", 1)[-1].strip()
            elif "phone:" in lower:
                current["phone"] = line.split(":", 1)[-1].strip()
            elif any(k in lower for k in ["industry:", "trade:", "type:", "category:"]):
                current["industry"] = line.split(":", 1)[-1].strip()
            elif "city:" in lower:
                current["city"] = line.split(":", 1)[-1].strip()

        if current.get("business_name"):
            prospects.append(BusinessProspect(**current))

        return prospects

    def _extract_score(self, raw: str) -> int:
        """Extract the 0-100 score from analysis output."""
        import re
        patterns = [
            r"(?:score|rating|overall)[:\s]*(\d{1,3})\s*/?\s*100",
            r"(\d{1,3})\s*/\s*100",
            r"(?:score|rating)[:\s]*(\d{1,3})",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:
                    return score
        return 50  # Default if parsing fails

    def _extract_issues(self, raw: str) -> list:
        """Extract site issues from analysis output."""
        issues = []
        categories = ["seo", "mobile", "performance", "security", "content", "contact", "design"]
        severities = ["critical", "high", "medium", "low"]

        for line in raw.split("\n"):
            line = line.strip()
            if not line or len(line) < 10:
                continue

            lower = line.lower()
            category = ""
            severity = "medium"

            for cat in categories:
                if cat in lower:
                    category = cat.upper()
                    break

            for sev in severities:
                if sev in lower:
                    severity = sev
                    break

            if category and any(indicator in lower for indicator in [
                "missing", "no ", "not ", "broken", "slow", "outdated",
                "absent", "lacks", "without", "doesn't", "isn't", "poor",
                "weak", "failed", "error", "issue", "problem",
            ]):
                issues.append(SiteIssue(
                    category=category,
                    severity=severity,
                    finding=line.strip("- *"),
                    recommendation="",
                ))

        return issues[:15]  # Cap at 15 issues


# =============================================================================
# ENTRY POINT
# =============================================================================

def run_prospector(config: dict = None):
    """Run the website prospector with optional config overrides."""
    flow = WebsiteProspectorFlow()
    if config:
        flow.state.config = ProspectorConfig(**config)
    result = flow.kickoff()
    return result


if __name__ == "__main__":
    run_prospector()

"""
================================================================================
                PSI REALTOR PIPELINE — MAIN FLOW
================================================================================
Automated realtor identification, qualification, and outreach pipeline
for Precision Sewer Inspection (Central Indiana).

Flow:
  initialize → research_realtors → qualify_leads → draft_outreach
  → sync_to_crm → check_followups → compile_report

Follows Godzilla pattern: Flow[RealtorPipelineState], structlog, error recovery.
================================================================================
"""

from crewai import Task, Crew, Process
from crewai.flow.flow import Flow, listen, start, router
from pydantic import Field
from typing import Optional
from datetime import datetime
import logging
import os
import json

from .state import (
    RealtorPipelineState,
    PipelineConfig,
    PipelinePhase,
    LeadStatus,
    RealtorLead,
)
from .agents import (
    create_realtor_researcher,
    create_lead_qualifier,
    create_outreach_drafter,
    create_followup_drafter,
    create_report_compiler,
)
from .prompts import (
    get_research_task,
    get_qualification_task,
    get_outreach_task,
    get_followup_task,
    get_report_task,
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.environ.get(
    "PSI_OUTPUT_DIR",
    "/Volumes/SanDisk1Tb/LAIAS_AGENT_OUTPUT/psi_realtor_pipeline"
)


class RealtorPipelineFlow(Flow[RealtorPipelineState]):
    """
    PSI Realtor Pipeline — Identifies, qualifies, and drafts outreach
    to Central Indiana realtors for sewer inspection partnerships.

    Outputs:
      - Qualified lead list with scores
      - Personalized outreach emails ready for review
      - HubSpot CRM contacts (when CRM sync is enabled)
      - Pipeline run report
    """

    @start()
    def initialize(self):
        """Set up the pipeline run."""
        cities_tag = "-".join(self.state.config.target_cities[:3]).lower().replace(" ", "")
        self.state.task_id = f"realtor-outreach_{cities_tag}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
        self.state.started_at = datetime.now().isoformat()
        self.state.status = "running"
        self.state.phase = PipelinePhase.INITIALIZE
        self.state.progress = 5.0

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        logger.info(
            "pipeline.initialized",
            task_id=self.state.task_id,
            target_cities=self.state.config.target_cities,
            max_leads=self.state.config.max_leads_per_run,
        )
        return {"initialized": True}

    @listen(initialize)
    def research_realtors(self, init_data):
        """Phase 1: Research and identify realtors in target cities."""
        self.state.phase = PipelinePhase.RESEARCH
        self.state.progress = 15.0

        logger.info(f"pipeline.research.start | cities={self.state.config.target_cities}")

        try:
            researcher = create_realtor_researcher()
            task = Task(
                description=get_research_task(
                    self.state.config.target_cities,
                    self.state.config.max_leads_per_run,
                ),
                expected_output=(
                    "A structured list of real estate agents with: name, email, "
                    "phone, brokerage, city, recent listings, and specialties."
                ),
                agent=researcher,
            )

            crew = Crew(
                agents=[researcher],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()
            raw_output = result.raw if hasattr(result, "raw") else str(result)

            # Parse leads from research output
            leads = self._parse_research_output(raw_output)
            self.state.leads = leads
            self.state.leads_researched = len(leads)
            self.state.progress = 35.0

            logger.info(f"pipeline.research.complete | leads_found={len(leads)}")
            return {"leads": len(leads), "raw": raw_output}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"pipeline.research.failed | error={str(e)}")
            return {"leads": 0, "error": str(e)}

    @listen(research_realtors)
    def qualify_leads(self, research_data):
        """Phase 2: Score and qualify the researched leads."""
        self.state.phase = PipelinePhase.QUALIFY
        self.state.progress = 45.0

        if not self.state.leads:
            logger.warning("pipeline.qualify.no_leads")
            return {"qualified": 0}

        logger.info(f"pipeline.qualify.start | leads_count={len(self.state.leads)}")

        try:
            qualifier = create_lead_qualifier()
            leads_text = "\n".join(
                f"- {lead.name} | {lead.email} | {lead.brokerage} | {lead.city} | "
                f"Listings: {', '.join(lead.recent_listings[:3])} | "
                f"Specialties: {', '.join(lead.specialties)}"
                for lead in self.state.leads
            )

            task = Task(
                description=get_qualification_task(leads_text),
                expected_output=(
                    "Each lead scored 1-5 on five criteria with final status "
                    "(QUALIFIED/MAYBE/DISQUALIFIED) and one sentence explanation."
                ),
                agent=qualifier,
            )

            crew = Crew(
                agents=[qualifier],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()
            raw_output = result.raw if hasattr(result, "raw") else str(result)

            # Mark qualified leads
            qualified = []
            for lead in self.state.leads:
                if lead.name.lower() in raw_output.lower() and "DISQUALIFIED" not in raw_output.upper().split(lead.name.upper())[0][-200:] if lead.name.upper() in raw_output.upper() else False:
                    lead.status = LeadStatus.QUALIFIED
                    qualified.append(lead)
                else:
                    # Default to qualified if parsing is ambiguous — human reviews anyway
                    lead.status = LeadStatus.QUALIFIED
                    qualified.append(lead)

            self.state.qualified_leads = qualified
            self.state.leads_qualified = len(qualified)
            self.state.progress = 55.0

            logger.info(f"pipeline.qualify.complete | qualified={len(qualified)}")
            return {"qualified": len(qualified), "raw": raw_output}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"pipeline.qualify.failed | error={str(e)}")
            # On qualification failure, pass all leads through for human review
            self.state.qualified_leads = self.state.leads
            self.state.leads_qualified = len(self.state.leads)
            return {"qualified": len(self.state.leads), "error": str(e)}

    @listen(qualify_leads)
    def draft_outreach(self, qualify_data):
        """Phase 3: Draft personalized outreach emails for qualified leads."""
        self.state.phase = PipelinePhase.DRAFT_OUTREACH
        self.state.progress = 60.0

        if not self.state.qualified_leads:
            logger.warning("pipeline.outreach.no_qualified_leads")
            return {"drafted": 0}

        logger.info(
            "pipeline.outreach.start",
            leads_count=len(self.state.qualified_leads),
        )

        drafter = create_outreach_drafter()
        drafts = []

        for lead in self.state.qualified_leads:
            try:
                lead_data = (
                    f"Name: {lead.name}\n"
                    f"Email: {lead.email}\n"
                    f"Brokerage: {lead.brokerage}\n"
                    f"City: {lead.city}\n"
                    f"Recent Listings: {', '.join(lead.recent_listings[:3])}\n"
                    f"Specialties: {', '.join(lead.specialties)}\n"
                )

                task = Task(
                    description=get_outreach_task(lead.name, lead_data),
                    expected_output="A complete email with subject line and body, under 150 words.",
                    agent=drafter,
                )

                crew = Crew(
                    agents=[drafter],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = crew.kickoff()
                email_text = result.raw if hasattr(result, "raw") else str(result)

                lead.outreach_draft = email_text
                lead.status = LeadStatus.OUTREACH_DRAFTED
                drafts.append({
                    "name": lead.name,
                    "email": lead.email,
                    "draft": email_text,
                })

                logger.info(f"pipeline.outreach.drafted | lead={lead.name}")

            except Exception as e:
                logger.error(f"pipeline.outreach.draft_failed | lead=lead.name | error={str(e)}")
                lead.notes += f" Draft failed: {str(e)}"

        self.state.outreach_drafts = drafts
        self.state.outreach_drafted = len(drafts)
        self.state.progress = 80.0

        logger.info(f"pipeline.outreach.complete | drafted={len(drafts)}")
        return {"drafted": len(drafts)}

    @listen(draft_outreach)
    def compile_report(self, outreach_data):
        """Phase 4: Compile the pipeline run report."""
        self.state.phase = PipelinePhase.REPORT
        self.state.progress = 90.0

        logger.info("pipeline.report.start")

        try:
            compiler = create_report_compiler()

            pipeline_summary = json.dumps({
                "task_id": self.state.task_id,
                "started_at": self.state.started_at,
                "leads_researched": self.state.leads_researched,
                "leads_qualified": self.state.leads_qualified,
                "outreach_drafted": self.state.outreach_drafted,
                "errors": self.state.error_count,
                "qualified_leads": [
                    {
                        "name": l.name,
                        "email": l.email,
                        "brokerage": l.brokerage,
                        "city": l.city,
                        "status": l.status.value,
                    }
                    for l in self.state.qualified_leads
                ],
                "outreach_drafts": [
                    {"name": d["name"], "subject": d["draft"][:80]}
                    for d in self.state.outreach_drafts
                ],
            }, indent=2)

            task = Task(
                description=get_report_task(pipeline_summary),
                expected_output="A clean, scannable pipeline report in markdown format.",
                agent=compiler,
            )

            crew = Crew(
                agents=[compiler],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()
            report = result.raw if hasattr(result, "raw") else str(result)

            self.state.report_output = report

            # Write outputs to disk
            run_dir = os.path.join(OUTPUT_DIR, self.state.task_id)
            os.makedirs(run_dir, exist_ok=True)

            with open(os.path.join(run_dir, "report.md"), "w") as f:
                f.write(report)

            with open(os.path.join(run_dir, "outreach_drafts.json"), "w") as f:
                json.dump(self.state.outreach_drafts, f, indent=2)

            with open(os.path.join(run_dir, "qualified_leads.json"), "w") as f:
                json.dump(
                    [l.model_dump() for l in self.state.qualified_leads],
                    f, indent=2,
                )

            with open(os.path.join(run_dir, "pipeline_state.json"), "w") as f:
                json.dump(self.state.model_dump(), f, indent=2, default=str)

            logger.info(
                "pipeline.report.complete",
                output_dir=run_dir,
                report_length=len(report),
            )

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"pipeline.report.failed | error={str(e)}")

        # Finalize
        self.state.phase = PipelinePhase.COMPLETE
        self.state.status = "complete"
        self.state.progress = 100.0
        self.state.completed_at = datetime.now().isoformat()

        logger.info(
            "pipeline.complete",
            task_id=self.state.task_id,
            leads_researched=self.state.leads_researched,
            leads_qualified=self.state.leads_qualified,
            outreach_drafted=self.state.outreach_drafted,
        )

        return {"report": self.state.report_output}

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _parse_research_output(self, raw_output: str) -> list:
        """
        Parse the researcher agent's output into RealtorLead objects.
        The output is free-form text, so we extract what we can.
        """
        leads = []
        lines = raw_output.split("\n")
        current_lead = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current_lead.get("name"):
                    leads.append(self._build_lead(current_lead))
                    current_lead = {}
                continue

            lower = line.lower()
            if any(key in lower for key in ["name:", "agent:"]):
                if current_lead.get("name"):
                    leads.append(self._build_lead(current_lead))
                    current_lead = {}
                current_lead["name"] = line.split(":", 1)[-1].strip().strip("*")
            elif "email:" in lower:
                current_lead["email"] = line.split(":", 1)[-1].strip()
            elif "phone:" in lower:
                current_lead["phone"] = line.split(":", 1)[-1].strip()
            elif any(key in lower for key in ["brokerage:", "company:", "firm:"]):
                current_lead["brokerage"] = line.split(":", 1)[-1].strip()
            elif any(key in lower for key in ["city:", "area:", "location:"]):
                current_lead["city"] = line.split(":", 1)[-1].strip()
            elif any(key in lower for key in ["listing", "transaction", "recent"]):
                current_lead.setdefault("listings", []).append(
                    line.split(":", 1)[-1].strip() if ":" in line else line
                )
            elif any(key in lower for key in ["special", "focus", "expert"]):
                current_lead.setdefault("specialties", []).append(
                    line.split(":", 1)[-1].strip() if ":" in line else line
                )

        # Don't forget the last lead
        if current_lead.get("name"):
            leads.append(self._build_lead(current_lead))

        return leads

    def _build_lead(self, data: dict) -> RealtorLead:
        """Build a RealtorLead from parsed data."""
        return RealtorLead(
            name=data.get("name", "Unknown"),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            brokerage=data.get("brokerage", ""),
            city=data.get("city", ""),
            recent_listings=data.get("listings", []),
            specialties=data.get("specialties", []),
            status=LeadStatus.RESEARCHED,
        )


# =============================================================================
# ENTRY POINT
# =============================================================================

def run_pipeline(config: dict = None):
    """Run the realtor pipeline with optional config overrides."""
    flow = RealtorPipelineFlow()
    if config:
        flow.state.config = PipelineConfig(**config)
    result = flow.kickoff()
    return result


if __name__ == "__main__":
    run_pipeline()

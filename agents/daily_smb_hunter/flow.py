"""
================================================================================
            DAILY SMB HUNTER — MAIN FLOW
================================================================================
Runs once daily. Finds one SMB in Southport IN, builds complete intelligence,
designs the agent solution, writes the agent code, and packages everything
Ryan needs to close the deal.

Flow:
  initialize → hunt_target → deep_research → design_solution
  → build_agent → create_sales_package → finalize

Output: /Volumes/SanDisk1Tb/LAIAS_AGENT_OUTPUT/daily_smb_hunter/
================================================================================
"""

from crewai import Task, Crew, Process
from crewai.flow.flow import Flow, listen, start
from datetime import datetime
import logging
import os
import json

from .state import (
    HunterState,
    HunterConfig,
    HunterPhase,
    BusinessTarget,
    OwnerProfile,
    SolutionSpec,
    SalesPackage,
)
from .agents import (
    create_business_scout,
    create_deep_researcher,
    create_solution_architect,
    create_agent_builder,
    create_sales_packager,
    create_ad_copywriter,
)
from .prompts import (
    get_scout_task,
    get_deep_research_task,
    get_solution_design_task,
    get_agent_build_task,
    get_sales_package_task,
    get_ad_copy_task,
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.environ.get(
    "HUNTER_OUTPUT_DIR",
    "/Volumes/SanDisk1Tb/LAIAS_AGENT_OUTPUT/daily_smb_hunter"
)


class DailyHunterFlow(Flow[HunterState]):
    """
    Daily SMB Hunter — Every day at 7 PM, finds one local business,
    researches them completely, designs their agent solution, builds it,
    and packages the sales materials for Ryan.
    """

    @start()
    def initialize(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.state.hunt_date = today
        self.state.task_id = f"hunt_{today}_{datetime.now().strftime('%H%M%S')}"
        self.state.started_at = datetime.now().isoformat()
        self.state.status = "running"
        self.state.phase = HunterPhase.INITIALIZE
        self.state.progress = 5.0

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        logger.info(f"hunter.initialized | task_id=self.state.task_id | date={today}")
        return {"date": today}

    @listen(initialize)
    def hunt_target(self, init_data):
        """Phase 1: Find today's target business."""
        self.state.phase = HunterPhase.HUNT
        self.state.progress = 10.0

        # Load previous targets to avoid duplicates
        exclusions = self._load_history()

        logger.info(f"hunter.hunt.start | exclusion_count={len(exclusions)}")

        try:
            scout = create_business_scout()
            task = Task(
                description=get_scout_task(
                    self.state.config.target_area,
                    self.state.config.industries_priority,
                    exclusions,
                ),
                expected_output=(
                    "One specific business with: name, industry, address, phone, "
                    "email, website, Google rating, review count, owner name, "
                    "and why they're the best target."
                ),
                agent=scout,
            )

            crew = Crew(agents=[scout], tasks=[task], process=Process.sequential, verbose=True)
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)

            target = self._parse_target(raw)
            self.state.target = target
            self.state.progress = 20.0

            logger.info(f"hunter.hunt.complete | target={target.business_name}")
            return {"target": target.business_name, "raw": raw}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"hunter.hunt.failed | error={str(e)}")
            return {"error": str(e)}

    @listen(hunt_target)
    def deep_research(self, hunt_data):
        """Phase 2: Deep dive on the target business."""
        self.state.phase = HunterPhase.DEEP_RESEARCH
        self.state.progress = 25.0

        if not self.state.target.business_name:
            logger.warning("hunter.research.no_target")
            return {"error": "No target found"}

        logger.info(f"hunter.research.start | target={self.state.target.business_name}")

        try:
            researcher = create_deep_researcher()
            task = Task(
                description=get_deep_research_task(
                    self.state.target.business_name,
                    self.state.target.industry,
                    self.state.target.address,
                    self.state.target.website,
                ),
                expected_output=(
                    "Complete intelligence report: owner profile, business profile, "
                    "online presence, competitive landscape, and pain points."
                ),
                agent=researcher,
            )

            crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential, verbose=True)
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)

            # Enrich target with research findings
            self._enrich_target(raw)
            self.state.progress = 40.0

            logger.info(f"hunter.research.complete | target={self.state.target.business_name}")
            return {"intel": raw}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"hunter.research.failed | error={str(e)}")
            return {"error": str(e)}

    @listen(deep_research)
    def design_solution(self, research_data):
        """Phase 3: Design the exact agent solution."""
        self.state.phase = HunterPhase.SOLUTION_DESIGN
        self.state.progress = 45.0

        intel = research_data.get("intel", "")
        if not intel:
            intel = json.dumps(self.state.target.model_dump(), indent=2, default=str)

        logger.info("hunter.solution.start")

        try:
            architect = create_solution_architect()
            task = Task(
                description=get_solution_design_task(
                    intel,
                    self.state.config.min_revenue_impact,
                ),
                expected_output=(
                    "Complete solution design with revenue math, agent requirements, "
                    "and pricing recommendation."
                ),
                agent=architect,
            )

            crew = Crew(agents=[architect], tasks=[task], process=Process.sequential, verbose=True)
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)

            self._parse_solution(raw)
            self.state.progress = 55.0

            logger.info(f"hunter.solution.complete | solution={self.state.solution.solution_name}")
            return {"solution": raw}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"hunter.solution.failed | error={str(e)}")
            return {"error": str(e)}

    @listen(design_solution)
    def build_agent(self, solution_data):
        """Phase 4: Generate the actual agent code."""
        self.state.phase = HunterPhase.AGENT_BUILD
        self.state.progress = 60.0

        solution = solution_data.get("solution", "")
        if not solution:
            solution = json.dumps(self.state.solution.model_dump(), indent=2, default=str)

        logger.info("hunter.build.start")

        try:
            builder = create_agent_builder()
            task = Task(
                description=get_agent_build_task(solution, self.state.target.business_name),
                expected_output="Complete Python code for all agent files: state.py, agents.py, prompts.py, flow.py, __init__.py",
                agent=builder,
            )

            crew = Crew(agents=[builder], tasks=[task], process=Process.sequential, verbose=True)
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)

            self.state.generated_agent_code = raw
            self.state.progress = 75.0

            logger.info(f"hunter.build.complete | code_length={len(raw)}")
            return {"agent_code": raw}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"hunter.build.failed | error={str(e)}")
            return {"error": str(e)}

    @listen(build_agent)
    def create_sales_package(self, build_data):
        """Phase 5: Create Ryan's complete sales package + ad copy."""
        self.state.phase = HunterPhase.SALES_PACKAGE
        self.state.progress = 80.0

        intel = json.dumps(self.state.target.model_dump(), indent=2, default=str)
        solution = json.dumps(self.state.solution.model_dump(), indent=2, default=str)
        config_dict = self.state.config.model_dump()

        logger.info("hunter.sales.start")

        try:
            # Sales package
            packager = create_sales_packager()
            sales_task = Task(
                description=get_sales_package_task(intel, solution, config_dict),
                expected_output="Complete sales package with all 10 components.",
                agent=packager,
            )

            # Ad copy
            copywriter = create_ad_copywriter()
            ad_task = Task(
                description=get_ad_copy_task(intel, solution),
                expected_output="Cold email, social ad, and printable one-pager.",
                agent=copywriter,
            )

            crew = Crew(
                agents=[packager, copywriter],
                tasks=[sales_task, ad_task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()

            # Extract outputs
            sales_output = ""
            ad_output = ""
            for task_output in result.tasks_output if hasattr(result, "tasks_output") else []:
                raw = task_output.raw if hasattr(task_output, "raw") else str(task_output)
                if "voicemail" in raw.lower() or "objection" in raw.lower():
                    sales_output = raw
                else:
                    ad_output = raw

            if not sales_output:
                sales_output = result.raw if hasattr(result, "raw") else str(result)

            self.state.progress = 90.0
            logger.info("hunter.sales.complete")

            # Write everything to disk
            self._write_outputs(sales_output, ad_output)

            return {"sales": sales_output, "ads": ad_output}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"hunter.sales.failed | error={str(e)}")
            # Still write what we have
            self._write_outputs("", "")
            return {"error": str(e)}

    @listen(create_sales_package)
    def finalize(self, sales_data):
        """Final phase: Update history, set status."""
        self._update_history()

        self.state.phase = HunterPhase.COMPLETE
        self.state.status = "complete"
        self.state.progress = 100.0
        self.state.completed_at = datetime.now().isoformat()

        logger.info(
            "hunter.complete",
            task_id=self.state.task_id,
            target=self.state.target.business_name,
            solution=self.state.solution.solution_name,
        )
        return {"target": self.state.target.business_name}

    # =========================================================================
    # OUTPUT & HISTORY
    # =========================================================================

    def _write_outputs(self, sales_output: str, ad_output: str):
        """Write all outputs to the run directory."""
        biz_name = self.state.target.business_name.lower().replace(" ", "-").replace("'", "")[:40]
        run_name = f"{self.state.hunt_date}_{biz_name}_{self.state.target.industry.lower()}"
        run_dir = os.path.join(OUTPUT_DIR, run_name)
        os.makedirs(run_dir, exist_ok=True)

        self.state.generated_agent_path = run_dir

        # Business intel
        with open(os.path.join(run_dir, "business_intelligence.json"), "w") as f:
            json.dump(self.state.target.model_dump(), f, indent=2, default=str)

        # Solution design
        with open(os.path.join(run_dir, "solution_design.json"), "w") as f:
            json.dump(self.state.solution.model_dump(), f, indent=2, default=str)

        # Generated agent code
        if self.state.generated_agent_code:
            with open(os.path.join(run_dir, "generated_agent_code.py"), "w") as f:
                f.write(self.state.generated_agent_code)

        # Sales package
        if sales_output:
            with open(os.path.join(run_dir, "ryans_sales_package.md"), "w") as f:
                f.write(f"# Sales Package: {self.state.target.business_name}\n")
                f.write(f"**Generated:** {self.state.hunt_date}\n")
                f.write(f"**Industry:** {self.state.target.industry}\n")
                f.write(f"**Location:** {self.state.target.address}\n\n")
                f.write(sales_output)

        # Ad copy
        if ad_output:
            with open(os.path.join(run_dir, "ad_copy_and_materials.md"), "w") as f:
                f.write(f"# Marketing Materials: {self.state.target.business_name}\n\n")
                f.write(ad_output)

        # Ryan's quick reference card (the thing he reads on the drive over)
        with open(os.path.join(run_dir, "RYAN_READ_THIS_FIRST.md"), "w") as f:
            t = self.state.target
            s = self.state.solution
            f.write(f"# TODAY'S TARGET: {t.business_name}\n\n")
            f.write(f"**What they do:** {t.industry}\n")
            f.write(f"**Where:** {t.address}\n")
            f.write(f"**Phone:** {t.phone}\n")
            f.write(f"**Owner:** {t.owner.name}\n")
            f.write(f"**Estimated Revenue:** {t.estimated_annual_revenue}\n")
            f.write(f"**Google:** {t.google_rating} stars, {t.review_count} reviews\n")
            f.write(f"**Website:** {t.website}\n\n")
            f.write(f"## THE PITCH\n")
            f.write(f"**Solution:** {s.solution_name}\n")
            f.write(f"**What it does:** {s.how_it_works}\n")
            f.write(f"**Revenue impact:** {s.projected_annual_impact} ({s.projected_roi_percentage})\n")
            f.write(f"**Setup:** {s.setup_fee} | **Monthly:** {s.monthly_fee}\n")
            f.write(f"**ROI timeline:** {s.roi_timeline}\n\n")
            f.write(f"## OWNER INTEL\n")
            f.write(f"**Background:** {t.owner.background}\n")
            f.write(f"**Pain points:** {', '.join(t.owner.pain_points)}\n")
            f.write(f"**What motivates them:** {', '.join(t.owner.motivators)}\n\n")
            f.write(f"## COMPETITORS\n")
            for c in t.competitors[:5]:
                f.write(f"- {c}\n")

        # Full pipeline state
        with open(os.path.join(run_dir, "pipeline_state.json"), "w") as f:
            json.dump(self.state.model_dump(), f, indent=2, default=str)

        logger.info(f"hunter.outputs.written | dir={run_dir}")

    def _load_history(self) -> list:
        """Load previously targeted businesses to avoid duplicates."""
        history_file = self.state.config.history_file
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                return json.load(f)
        return []

    def _update_history(self):
        """Add today's target to the history file."""
        history_file = self.state.config.history_file
        os.makedirs(os.path.dirname(history_file), exist_ok=True)

        history = self._load_history()
        history.append(self.state.target.business_name)

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    # =========================================================================
    # PARSERS
    # =========================================================================

    def _parse_target(self, raw: str) -> BusinessTarget:
        """Parse scout output into a BusinessTarget."""
        target = BusinessTarget()
        for line in raw.split("\n"):
            line = line.strip()
            lower = line.lower()
            if any(k in lower for k in ["business name:", "business:", "name:"]) and not target.business_name:
                target.business_name = line.split(":", 1)[-1].strip().strip("*")
            elif "industry:" in lower or "trade:" in lower or "type:" in lower:
                target.industry = line.split(":", 1)[-1].strip()
            elif "address:" in lower or "location:" in lower:
                target.address = line.split(":", 1)[-1].strip()
            elif "phone:" in lower:
                target.phone = line.split(":", 1)[-1].strip()
            elif "email:" in lower:
                target.email = line.split(":", 1)[-1].strip()
            elif any(k in lower for k in ["website:", "url:", "site:"]):
                for token in line.split():
                    if "http" in token or "www." in token or ".com" in token:
                        target.website = token.strip("*,;()[]")
                        break
            elif "rating:" in lower or "stars" in lower:
                target.google_rating = line.split(":", 1)[-1].strip() if ":" in line else line
            elif "review" in lower and any(c.isdigit() for c in line):
                import re
                nums = re.findall(r"\d+", line)
                if nums:
                    target.review_count = int(nums[0])
            elif "owner:" in lower:
                target.owner.name = line.split(":", 1)[-1].strip().strip("*")
        return target

    def _enrich_target(self, raw: str):
        """Enrich target with deep research findings."""
        t = self.state.target
        lower_raw = raw.lower()

        # Try to extract revenue estimate
        import re
        rev_patterns = [
            r"\$(\d{1,3}(?:,\d{3})*(?:K|k)?)\s*(?:-|to)\s*\$?(\d{1,3}(?:,\d{3})*(?:K|k)?)\s*(?:/year|annually|per year|revenue)",
            r"estimated.*?revenue.*?\$(\d{1,3}(?:,\d{3})*(?:K|k)?)",
            r"revenue.*?\$(\d{1,3}(?:,\d{3})*(?:K|k)?)",
        ]
        for pattern in rev_patterns:
            match = re.search(pattern, raw, re.IGNORECASE)
            if match:
                t.estimated_annual_revenue = match.group(0).strip()
                break

        # Extract employee count
        emp_match = re.search(r"(\d{1,3})\s*employees", raw, re.IGNORECASE)
        if emp_match:
            t.estimated_employees = int(emp_match.group(1))

        # Store the full research as notes for reference
        # Extract pain points and strengths from the text
        for line in raw.split("\n"):
            line = line.strip("- *")
            ll = line.lower()
            if any(w in ll for w in ["weakness", "problem", "issue", "lacks", "missing", "no ", "poor"]):
                t.current_weaknesses.append(line[:200])
            elif any(w in ll for w in ["strength", "strong", "good", "excellent", "positive"]):
                t.current_strengths.append(line[:200])
            elif any(w in ll for w in ["competitor", "competing", "rival"]):
                t.competitors.append(line[:200])

    def _parse_solution(self, raw: str):
        """Parse solution architect output."""
        s = self.state.solution
        for line in raw.split("\n"):
            line = line.strip()
            lower = line.lower()
            if "solution name:" in lower:
                s.solution_name = line.split(":", 1)[-1].strip().strip("*")
            elif "type:" in lower and not s.solution_type:
                s.solution_type = line.split(":", 1)[-1].strip()
            elif "revenue strategy:" in lower:
                s.revenue_strategy = line.split(":", 1)[-1].strip()
            elif "annual impact:" in lower or "projected" in lower and "impact" in lower:
                s.projected_annual_impact = line.split(":", 1)[-1].strip()
            elif "roi" in lower and "%" in line:
                s.projected_roi_percentage = line.split(":", 1)[-1].strip()
            elif "setup:" in lower or "setup fee:" in lower:
                s.setup_fee = line.split(":", 1)[-1].strip()
            elif "monthly:" in lower or "monthly fee:" in lower:
                s.monthly_fee = line.split(":", 1)[-1].strip()
            elif "roi timeline:" in lower or "break even" in lower:
                s.roi_timeline = line.split(":", 1)[-1].strip()

        # Store full output as how_it_works
        s.how_it_works = raw[:2000]


# =============================================================================
# ENTRY POINT
# =============================================================================

def run_hunter(config: dict = None):
    """Run the daily hunter with optional config overrides."""
    flow = DailyHunterFlow()
    if config:
        flow.state.config = HunterConfig(**config)
    result = flow.kickoff()
    return result


if __name__ == "__main__":
    run_hunter()

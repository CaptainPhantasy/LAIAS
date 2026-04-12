"""
================================================================================
            SOCIAL MEDIA OPERATOR — MAIN FLOW
================================================================================
Creates content, adapts per platform, finds prospects via social signals.
Content gets drafted to files for review. Browser posting is a separate step
that requires Douglas to approve.

Flow:
  initialize → create_content → adapt_per_platform → prospect → compile

Output: /Volumes/SanDisk1Tb/LAIAS_AGENT_OUTPUT/social_media_operator/
================================================================================
"""

from crewai import Task, Crew, Process
from crewai.flow.flow import Flow, listen, start
from datetime import datetime
import logging
import os
import json

from .state import (
    OperatorState,
    SocialConfig,
    ContentBatch,
    SocialPost,
    ProspectLead,
    Platform,
    PostStatus,
)
from .agents import (
    create_content_strategist,
    create_platform_adapter,
    create_social_prospector,
)
from .prompts import (
    get_content_strategy_task,
    get_platform_adapt_task,
    get_prospecting_task,
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.environ.get(
    "SOCIAL_OUTPUT_DIR",
    "/Volumes/SanDisk1Tb/LAIAS_AGENT_OUTPUT/social_media_operator"
)


class SocialMediaFlow(Flow[OperatorState]):
    """
    Social Media Operator — Creates a week of content, adapts per platform,
    and finds prospects. All content is drafted to files for Douglas to
    review before posting.
    """

    @start()
    def initialize(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.state.task_id = f"social-content_{today}"
        self.state.started_at = datetime.now().isoformat()
        self.state.status = "running"
        self.state.progress = 5.0

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logger.info(f"social.initialized | task_id={self.state.task_id}")
        return {"date": today}

    @listen(initialize)
    def create_content(self, init_data):
        """Phase 1: Generate content ideas for the week."""
        self.state.progress = 15.0
        logger.info("social.content.start")

        try:
            strategist = create_content_strategist()
            task = Task(
                description=get_content_strategy_task(
                    self.state.config.topics,
                    self.state.config.never,
                    self.state.config.posts_per_week,
                ),
                expected_output=(
                    f"{self.state.config.posts_per_week} content ideas with theme, "
                    "core message, content type, hook, body, and call to action."
                ),
                agent=strategist,
            )

            crew = Crew(agents=[strategist], tasks=[task], process=Process.sequential, verbose=True)
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)

            self.state.progress = 35.0
            logger.info(f"social.content.complete | length={len(raw)}")
            return {"content_ideas": raw}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"social.content.failed | error={str(e)}")
            return {"error": str(e)}

    @listen(create_content)
    def adapt_per_platform(self, content_data):
        """Phase 2: Adapt each content idea for all 5 platforms."""
        self.state.progress = 40.0
        content_ideas = content_data.get("content_ideas", "")

        if not content_ideas:
            logger.warning("social.adapt.no_content")
            return {"adapted": 0}

        logger.info("social.adapt.start")

        try:
            adapter = create_platform_adapter()
            task = Task(
                description=get_platform_adapt_task(content_ideas),
                expected_output=(
                    "Each content idea adapted for Twitter, LinkedIn, Instagram, "
                    "Facebook, and TikTok with platform-native formatting."
                ),
                agent=adapter,
            )

            crew = Crew(agents=[adapter], tasks=[task], process=Process.sequential, verbose=True)
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)

            # Parse into content batches
            self._parse_adapted_content(raw)
            self.state.progress = 65.0
            logger.info(f"social.adapt.complete | batches={len(self.state.content_batches)}")
            return {"adapted": raw}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"social.adapt.failed | error={str(e)}")
            return {"error": str(e)}

    @listen(adapt_per_platform)
    def prospect(self, adapt_data):
        """Phase 3: Find social media prospects."""
        self.state.progress = 70.0
        logger.info("social.prospect.start")

        try:
            prospector = create_social_prospector()
            task = Task(
                description=get_prospecting_task(
                    ["Twitter", "LinkedIn", "Facebook"],
                    [
                        "plumbing", "HVAC", "electrician", "roofing",
                        "dental", "salon", "restaurant", "auto repair",
                        "real estate", "home inspection",
                    ],
                    "Indianapolis, Indiana and surrounding areas",
                ),
                expected_output=(
                    "5-10 social media signals from local business owners who "
                    "might need Legacy AI's services, with engagement suggestions."
                ),
                agent=prospector,
            )

            crew = Crew(agents=[prospector], tasks=[task], process=Process.sequential, verbose=True)
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)

            self.state.progress = 85.0
            logger.info(f"social.prospect.complete | length={len(raw)}")
            return {"prospects": raw}

        except Exception as e:
            self.state.error_count += 1
            self.state.last_error = str(e)
            logger.error(f"social.prospect.failed | error={str(e)}")
            return {"error": str(e)}

    @listen(prospect)
    def compile_output(self, prospect_data):
        """Phase 4: Write everything to the output directory."""
        self.state.progress = 90.0

        today = datetime.now().strftime("%Y-%m-%d")
        run_dir = os.path.join(OUTPUT_DIR, f"weekly-content_{today}")
        os.makedirs(run_dir, exist_ok=True)

        # === CONTENT CALENDAR ===
        with open(os.path.join(run_dir, "CONTENT_CALENDAR.md"), "w") as f:
            f.write(f"# Social Media Content Calendar — Week of {today}\n")
            f.write(f"**Brand:** Legacy AI / Floyd's Labs\n")
            f.write(f"**Author:** Douglas Talley\n\n")

            for i, batch in enumerate(self.state.content_batches, 1):
                f.write(f"## Post {i}: {batch.theme}\n\n")
                for post in batch.posts:
                    f.write(f"### {post.platform.value.upper()}\n")
                    f.write(f"{post.text}\n\n")
                    if post.hashtags:
                        f.write(f"**Hashtags:** {' '.join(post.hashtags)}\n\n")
                    f.write("---\n\n")

        # === PLATFORM-SPECIFIC FILES (ready to copy-paste) ===
        for platform in Platform:
            platform_posts = []
            for batch in self.state.content_batches:
                for post in batch.posts:
                    if post.platform == platform:
                        platform_posts.append(post)

            if platform_posts:
                with open(os.path.join(run_dir, f"{platform.value}_posts.md"), "w") as f:
                    f.write(f"# {platform.value.upper()} Posts — Week of {today}\n\n")
                    for i, post in enumerate(platform_posts, 1):
                        f.write(f"## Post {i}\n")
                        f.write(f"{post.text}\n\n")
                        if post.hashtags:
                            f.write(f"{' '.join(post.hashtags)}\n\n")
                        f.write("---\n\n")

        # === PROSPECTS ===
        prospects_raw = prospect_data.get("prospects", "")
        if prospects_raw:
            with open(os.path.join(run_dir, "PROSPECTS.md"), "w") as f:
                f.write(f"# Social Media Prospects — {today}\n\n")
                f.write("These are people showing signals they need help. ")
                f.write("Engage genuinely, not salesy.\n\n")
                f.write(prospects_raw)

        # === QUICK ACTION FILE ===
        with open(os.path.join(run_dir, "DOUGLAS_DO_THIS.md"), "w") as f:
            f.write(f"# This Week's Social Media Actions\n\n")
            f.write(f"## Post Schedule\n")
            f.write(f"You have {len(self.state.content_batches)} posts ready.\n")
            f.write(f"Each post is adapted for all 5 platforms.\n")
            f.write(f"Open the platform-specific files and copy-paste.\n\n")
            f.write(f"## Prospecting\n")
            f.write(f"Check PROSPECTS.md for people to engage with.\n")
            f.write(f"Reply to their posts with value. Do not DM cold.\n\n")
            f.write(f"## Time Required\n")
            f.write(f"Posting: ~15 minutes (copy paste across 5 platforms)\n")
            f.write(f"Prospecting: ~20 minutes (genuine replies to 3-5 people)\n")
            f.write(f"Total: Under 40 minutes for the whole week.\n")

        # === FULL STATE ===
        with open(os.path.join(run_dir, "pipeline_state.json"), "w") as f:
            json.dump(self.state.model_dump(), f, indent=2, default=str)

        self.state.status = "complete"
        self.state.progress = 100.0
        self.state.completed_at = datetime.now().isoformat()

        logger.info(f"social.complete | output_dir={run_dir}")
        return {"output_dir": run_dir}

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _parse_adapted_content(self, raw: str):
        """Parse adapted content into ContentBatch objects."""
        batches = []
        current_batch = ContentBatch()
        current_post = None

        for line in raw.split("\n"):
            line_stripped = line.strip()
            lower = line_stripped.lower()

            # Detect new content idea / post number
            if any(lower.startswith(f"post {i}") or lower.startswith(f"**post {i}") or lower.startswith(f"## post {i}") or lower.startswith(f"{i}.") for i in range(1, 20)):
                if current_batch.posts:
                    batches.append(current_batch)
                current_batch = ContentBatch(theme=line_stripped[:80])
                continue

            # Detect platform headers
            for platform in Platform:
                pname = platform.value
                if pname in lower and ("**" in line_stripped or "##" in line_stripped or line_stripped.lower().startswith(pname)):
                    if current_post and current_post.text:
                        current_batch.posts.append(current_post)
                    current_post = SocialPost(platform=platform)
                    break
            else:
                # Regular content line — append to current post
                if current_post is not None and line_stripped:
                    if line_stripped.startswith("#") and len(line_stripped) < 50:
                        # Probably a hashtag line
                        tags = [t.strip() for t in line_stripped.split() if t.startswith("#")]
                        if tags:
                            current_post.hashtags.extend(tags)
                            continue
                    current_post.text += line_stripped + "\n"

        # Don't forget the last ones
        if current_post and current_post.text:
            current_batch.posts.append(current_post)
        if current_batch.posts:
            batches.append(current_batch)

        self.state.content_batches = batches
        self.state.posts_drafted = sum(len(b.posts) for b in batches)


# =============================================================================
# ENTRY POINT
# =============================================================================

def run_social(config: dict = None):
    """Run the social media operator."""
    flow = SocialMediaFlow()
    if config:
        flow.state.config = SocialConfig(**config)
    result = flow.kickoff()
    return result


if __name__ == "__main__":
    run_social()

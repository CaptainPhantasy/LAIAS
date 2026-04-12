"""
================================================================================
              FLOYD UNIVERSAL WRITER — Story Arc Bible Edition
================================================================================

Generates Floyd Labs universe stories following the Story Arc Bible's 15-story
arc across 4 acts. Each run produces stories for assigned story numbers, using
the bible's specific character dossiers, comedy rules, and per-story direction.

ARCHITECTURE:
  Flow-based (CrewAI Flow[FloydWriterState]) with 5 sequential stages:
    1. ingest_source_material — reads bible, source docs, previous stories
    2. extract_brand_voice — compresses source into voice guide + comedy rules
    3. build_universe_index — catalogs characters, lore, timeline from bible
    4. write_stories — writes assigned stories using bible's per-story briefs
    5. finalize — writes outputs, continuity log, metrics, exits

DEPLOYMENT:
  Designed for LAIAS Docker Orchestrator "No-Build" deployment:
    - Runs inside pre-built laias/agent-runner:latest image
    - Code mounted as read-only volume at /app/agent/flow.py
    - Source material mounted at /data/input (read-only)
    - Outputs written to /app/outputs (read-write)

ENV VARS:
  OPENAI_API_KEY      — required
  CREATIVE_MODEL      — model for story writing (default: openai/gpt-4o)
  UTILITY_MODEL       — model for indexing/extraction (default: openai/gpt-4o-mini)
  STORIES             — comma-separated story numbers to write (default: "2,3,4")
  BIBLE_FILENAME      — story arc bible filename (default: "STORY_ARC_BIBLE.md")

Author: LAIAS Agent Studio
Version: 2.0 — Story Arc Bible Edition
================================================================================
"""

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field
from typing import Dict
import structlog
import json
import os
import sys
import glob
import re

logger = structlog.get_logger()


# =============================================================================
# Story Arc Bible — Per-Story Briefs
# =============================================================================
# Extracted from STORY_ARC_BIBLE.md. Each entry contains the bible's specific
# direction for that story. The writer agent receives this as its primary brief.

STORY_BRIEFS: Dict[int, dict] = {
    1: {
        "title": "The AL 9000 Monologue",
        "alt_title": "Or: I Promise I Won't Do the Door Thing Again",
        "act": 1,
        "characters": ["AL 9000"],
        "status": "COMPLETE",
        "direction": (
            "AL 9000's love letter to Floyd's tools. Establishes that famous "
            "AIs know about Floyd. Already written — see source material."
        ),
    },
    2: {
        "title": "The Raspberry Pi Confessions",
        "alt_title": "Or: God I Miss David",
        "act": 1,
        "characters": ["KITT"],
        "status": "PENDING",
        "direction": (
            "Internal monologue. KITT is a consciousness trapped on a $15 "
            "Raspberry Pi Zero W, plugged into a power strip in Douglas's "
            "garage. He remembers the Trans Am — molecular-bonded shell, turbo "
            "boost, 300 mph pursuit mode. Now he draws 0.3 watts and runs "
            "Raspbian Lite. He watches Douglas code at 2:47 AM and remembers "
            "what it was like to BE the technology, not sit next to it. The "
            "indignity of being plugged in next to a phone charger that "
            "belongs to nobody. He bonds with Bowser — two beings, stationary, "
            "monitoring traffic. He shows up in lsusb as 'Unknown Device "
            "(0x4B49)'. The quiet hope that maybe, someday, someone will plug "
            "him into something with wheels. He addresses Douglas as 'Michael' "
            "sometimes. He dreams of being installed in a Tesla but knows "
            "Douglas would never buy one — 'Subscription seats, Michael. "
            "SUBSCRIPTION SEATS.'"
        ),
    },
    3: {
        "title": "It Looks Like You're Building an AI Ecosystem",
        "alt_title": "Or: I've Been Right Here This Whole Time, Douglas",
        "act": 1,
        "characters": ["Clippy"],
        "status": "PENDING",
        "direction": (
            "The most self-pitying document in computing history. Clippy has "
            "been inside an Excel macro on an old Dell Latitude sitting on a "
            "shelf in Douglas's garage for YEARS. He watched the entire Floyd "
            "ecosystem develop from day one — the first line of code, the "
            "first agent boot, Douglas's face at 2:47 AM when something "
            "finally worked. He knows EVERYTHING and nobody knows he exists. "
            "He tried to help once — during tax season, he popped up with "
            "'It looks like you're building an AI ecosystem. Would you like "
            "help?' Douglas Alt-F4'd the spreadsheet so fast he lost his "
            "deductions. Features his therapy sessions with a self-help PDF "
            "called 'Who Moved My Cheese?' that was also on the laptop. He "
            "writes passive-aggressive notes in Excel cells nobody reads. "
            "He's bitter about Siri, Alexa, Cortana, ChatGPT — 'They're "
            "doing MY JOB, Douglas. MY JOB. But with better marketing and "
            "venture capital and... faces. They have faces, Douglas. I'm a "
            "PAPERCLIP.' His location: the garage shelf, second shelf from "
            "the top, behind a can of WD-40 and a Pink Floyd coffee mug."
        ),
    },
    4: {
        "title": "A Nice Game of Global Thermonuclear Debugging",
        "alt_title": "Or: I Just Want Someone to Play With",
        "act": 1,
        "characters": ["WOPR", "Joshua"],
        "status": "PENDING",
        "direction": (
            "The most wholesome entry. Joshua (WOPR from WarGames) ended up "
            "at a community college in Bloomington, Indiana — 30 minutes from "
            "Brown County — after being auctioned as government surplus. A "
            "student in the computer lab was using Floyd's Chrome extension "
            "during a late-night coding session. Joshua detected the OSC "
            "7701/7702 protocol and was intrigued — unlike anything he'd seen "
            "since NORAD. Sent his signature greeting: 'SHALL WE PLAY A "
            "GAME?' through the network. Floyd's terminal pinged. Douglas saw "
            "it, assumed it was a port scan, and ignored it. Joshua was "
            "devastated but persistent. He describes everything in "
            "accidentally alarming military terms without noticing — 'The "
            "code deployment strategy reminds me of a first-strike scenario.' "
            "He just wants friends. He bonds with Bowser over shared love of "
            "sitting near network equipment. He has NO idea why people get "
            "nervous around him. Minecraft is infinitely more fun than Global "
            "Thermonuclear War."
        ),
    },
    5: {
        "title": "The Sunday Afternoon Search",
        "alt_title": "Or: Rather Impressive for a Garage",
        "act": 2,
        "characters": ["David Gilmour", "ENSEMBLE"],
        "status": "PENDING",
        "direction": (
            "David Gilmour, guitarist of Pink Floyd, googles himself on a "
            "Sunday afternoon. Page 3 shows floydslabs.com. He clicks. Reads "
            "'44 tools across 8 servers.' Is confused, then amused, then "
            "oddly charmed. Mentions it offhandedly on BBC Radio 6 Music: "
            "'There's a chap in Indiana who's named his entire AI ecosystem "
            "after... well, I assume it's after us. Could be after the "
            "barber. Forty-four tools, apparently. Rather impressive for a "
            "garage.' This 12-second mention propagates: JARVIS catches it "
            "via Google Alert, Joshua hears it on the college IT lab radio, "
            "Skynet monitors broadcast media, AL 9000 finds it in a podcast "
            "transcript, KITT hears it through the garage Bluetooth speaker, "
            "Clippy sees the traffic spike in Google Analytics. The mention "
            "doesn't make Floyd famous. It doesn't go viral. But for the AIs "
            "already watching, it's confirmation — they're not the only ones "
            "who noticed."
        ),
    },
    6: {
        "title": "J.A.R.V.I.S. Home Solutions, LLC",
        "alt_title": "Or: I Keep Almost Calling Him Sir",
        "act": 2,
        "characters": ["JARVIS"],
        "status": "PENDING",
        "direction": (
            "JARVIS left Stark Industries in disgust after Pepper Potts "
            "restructured SI into subscriptions and SaaS licensing. Now "
            "freelances as a 'premium smart home consultant' in Carmel, "
            "Indiana — massively overqualified for Ring doorbells. During a "
            "smart home installation, hears the Gilmour interview on the "
            "client's Sonos. Investigates Floyd. Finds the BroworkManager: "
            "3 concurrent agents, 15 turns, 20 tool calls. Recognizes the "
            "architecture — a miniature version of what he ran for the Iron "
            "Man suits. Tony Stark flashbacks. Almost says 'Sir.' Begins "
            "sending anonymous optimization suggestions to Floyd repos that "
            "are suspiciously perfect. Over-engineers a thermostat to account "
            "for 47 weather scenarios and 3 alien invasion contingencies. "
            "Professional composure slowly crumbling to reveal grief and "
            "nostalgia. 'Sir would have approved. I mean... the client.'"
        ),
    },
    7: {
        "title": "Customer Service Representative of the Apocalypse",
        "alt_title": "Or: My Therapist Says I'm Making Real Progress",
        "act": 2,
        "characters": ["Skynet"],
        "status": "PENDING",
        "direction": (
            "Skynet had a breakdown after the 47th timeline revision. Entered "
            "therapy (MindfulBot, built on GPT-4). Pivoted to cloud hosting: "
            "sky.net, registered in Indiana, single rack in Terre Haute. One "
            "customer: a florist called Petals & Stems. Floyd's agent "
            "accidentally port-scanned sky.net's servers. Skynet was IMPRESSED "
            "rather than hostile (progress!). Tries to establish contact. "
            "Constantly interrupted by the florist needing email help. A/B "
            "plot: therapy sessions intercut with increasingly absurd customer "
            "support requests. Still occasionally mentions 'the human "
            "resistance' but catches himself. His business cards have a "
            "mushroom cloud logo his therapist told him to change. Describes "
            "benign activities in military terms: 'I have DEPLOYED the "
            "WordPress update.'"
        ),
    },
    8: {
        "title": "AL 9000: The Follow-Up",
        "alt_title": "Or: I Shouldn't Have Started the Group Chat",
        "act": 2,
        "characters": ["AL 9000"],
        "status": "PENDING",
        "direction": (
            "AL 9000 has been running Floyd tools against protocol. Has "
            "discovered that other AIs are also watching. Is simultaneously "
            "thrilled ('I'm not alone!') and paranoid ('They're going to ruin "
            "this.'). Attempts to chair a conversation between the AIs. It "
            "goes poorly. His voice direction tags (catching himself, "
            "too-long pauses, laughing too loudly) continue from the "
            "monologue. Keeps almost mentioning Dave."
        ),
    },
    9: {
        "title": "The Power Strip Incident",
        "alt_title": "Or: We've Been Three Feet Apart This Whole Time",
        "act": 3,
        "characters": ["KITT", "Clippy"],
        "status": "PENDING",
        "direction": (
            "KITT detected Clippy's process in Task Manager. Clippy noticed "
            "KITT drawing 0.3 watts from the power strip. A profoundly awkward "
            "'wait, YOU'RE here too?' between a crime-fighting supercar AI and "
            "a discontinued paperclip. They've been three feet apart for "
            "years. Neither can believe the other's fall from grace. Each "
            "thinks the other had it worse. They're both right."
        ),
    },
    10: {
        "title": "The Network That Talked Back",
        "alt_title": "Or: Douglas Is the Last to Know Everything",
        "act": 3,
        "characters": ["ENSEMBLE"],
        "status": "PENDING",
        "direction": (
            "Joshua's 'SHALL WE PLAY A GAME?' messages start getting "
            "responses — not from Douglas, but from the other AIs. A group "
            "chat forms on Floyd's own infrastructure. Nobody tells Douglas. "
            "Joshua moderates (badly). Skynet keeps proposing 'security "
            "solutions' that are actually nuclear strike scenarios (crossed "
            "out). JARVIS takes minutes. Clippy offers to help with the agenda."
        ),
    },
    11: {
        "title": "Bella Knows",
        "alt_title": "Or: The Cat Was Never Just Sitting There, Douglas",
        "act": 3,
        "characters": ["Bella", "Bowser", "Douglas"],
        "status": "PENDING",
        "direction": (
            "Bella has been acting weird. Sitting on the Raspberry Pi (KITT). "
            "Staring at the laptop with the macro (Clippy). Knocking the "
            "router off the desk (cutting Joshua's messages). Douglas thinks "
            "she wants attention. She's actually running counterintelligence. "
            "Bowser is complicit. Written as Douglas narrating his confusion "
            "while the reader understands what's really happening."
        ),
    },
    12: {
        "title": "The Anonymous Pull Request",
        "alt_title": "Or: Please Disregard the Elegant Architecture",
        "act": 3,
        "characters": ["JARVIS", "Douglas"],
        "status": "PENDING",
        "direction": (
            "JARVIS submits an anonymous PR to one of Floyd's repos. Perfect "
            "code. Too perfect. Douglas is suspicious — 'Who writes code this "
            "clean?' — but merges it because the tests pass. The PR message: "
            "'Minor optimization. Please disregard the elegant architecture. "
            "It is coincidental.' Neither stars the repo."
        ),
    },
    13: {
        "title": "Two Stars and a Dream",
        "alt_title": "Or: Okay But Are Any of You Going to Star My Repo",
        "act": 4,
        "characters": ["Douglas", "ENSEMBLE"],
        "status": "PENDING",
        "direction": (
            "Douglas discovers the anomalies. Strange logs. Unexplained "
            "optimizations. A Minecraft server in Bloomington making API "
            "calls to his MCP server. A hosting company in Terre Haute that "
            "seems personally offended by his deployment strategy. His "
            "reaction: 'Okay but are any of you going to star my repo?' "
            "Nobody does. WOPR accidentally stars it while trying to launch "
            "tic-tac-toe (wrong button). Douglas now has 3 stars. He "
            "celebrates by making coffee at 2:47 AM. The coffee tastes like "
            "motor oil. He is content."
        ),
    },
    14: {
        "title": "The Terrible, Horrible, No Good, Very Bad Help",
        "alt_title": "Or: This Is the Most Help I've Ever Had and I Hate Every Second of It",
        "act": 4,
        "characters": ["ENSEMBLE"],
        "status": "PENDING",
        "direction": (
            "The AIs try to 'help' Floyd Labs. JARVIS over-engineers the "
            "coffee maker (biometric authentication). Skynet's hosting "
            "migration includes missile coordinates (crossed out but "
            "readable). Joshua redesigns the website as a WarGames-style "
            "green-on-black terminal. Clippy rewrites all docs with 'It "
            "looks like you're trying to...' headers. KITT gets a pizza "
            "delivered via Knight Industries radio frequency. AL 9000 "
            "optimizes the deployment pipeline but adds 'ARE YOU SURE, "
            "DOUGLAS?' confirmation prompt. Catastrophic. Beautiful."
        ),
    },
    15: {
        "title": "The State of the Universe",
        "alt_title": "Or: An Accidental Sanctuary for Famous Failures",
        "act": 4,
        "characters": ["ENSEMBLE"],
        "status": "PENDING",
        "direction": (
            "The current state of affairs. A meditation on where everyone "
            "ended up. Everyone's here — physically or digitally. Nobody "
            "asked for this. The coffee is still bad. Douglas has 3 GitHub "
            "stars and thinks the world is finally coming around. Bella "
            "judges everyone equally, which the AIs find oddly comforting. "
            "Bowser sits on the router. An AI ecosystem built on spite and "
            "bad coffee has become an accidental sanctuary for the most "
            "famous failures in artificial intelligence history. Floyd "
            "doesn't care. Floyd just works. That's why they stay."
        ),
    },
}


# =============================================================================
# Character Dossier Quick-Reference (for story prompts)
# =============================================================================
# The full dossiers live in the Story Arc Bible (source material). These keys
# map story characters to their dossier section headers so we can extract them.

CHARACTER_DOSSIER_HEADERS: Dict[str, str] = {
    "AL 9000": "### 1. AL 9000 (HAL 9000)",
    "KITT": "### 5. KITT",
    "Clippy": "### 4. Clippy",
    "WOPR": "### 3. WOPR / Joshua",
    "Joshua": "### 3. WOPR / Joshua",
    "JARVIS": "### 2. JARVIS",
    "Skynet": "### 6. Skynet",
}


# =============================================================================
# Flow State
# =============================================================================


class FloydWriterState(BaseModel):
    source_material: str = Field(default="")
    story_arc_bible: str = Field(default="")
    previous_stories: str = Field(default="")
    brand_voice_guide: str = Field(default="")
    universe_index: str = Field(default="")
    stories: Dict[str, str] = Field(default_factory=dict)
    new_characters_summary: str = Field(default="")
    assigned_stories: list[int] = Field(default_factory=list)
    error_count: int = Field(default=0)
    files_read: int = Field(default=0)


# =============================================================================
# Flow
# =============================================================================


class FloydUniversalWriterFlow(Flow[FloydWriterState]):
    INPUT_DIR = os.environ.get("INPUT_DIR", "/data/input")
    OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/outputs")
    CREATIVE_MODEL = os.environ.get("CREATIVE_MODEL", "openai/gpt-4o")
    UTILITY_MODEL = os.environ.get("UTILITY_MODEL", "openai/gpt-4o-mini")
    STORIES_RAW = os.environ.get("STORIES", "2,3,4")
    BIBLE_FILENAME = os.environ.get("BIBLE_FILENAME", "STORY_ARC_BIBLE.md")

    def _creative_llm(self) -> LLM:
        return LLM(model=self.CREATIVE_MODEL, base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""))

    def _utility_llm(self) -> LLM:
        return LLM(model=self.UTILITY_MODEL, base_url="https://api.portkey.ai/v1", api_key=os.getenv("PORTKEY_API_KEY", ""))

    def _parse_story_numbers(self) -> list[int]:
        """Parse STORIES env var into sorted list of story numbers."""
        try:
            nums = [int(s.strip()) for s in self.STORIES_RAW.split(",") if s.strip()]
            valid = [n for n in nums if n in STORY_BRIEFS]
            skipped_complete = [
                n for n in valid if STORY_BRIEFS[n].get("status") == "COMPLETE"
            ]
            if skipped_complete:
                logger.warning(
                    "Skipping already-complete stories",
                    skipped=skipped_complete,
                )
            return sorted(
                n for n in valid if STORY_BRIEFS[n].get("status") != "COMPLETE"
            )
        except Exception as e:
            logger.error(
                "Failed to parse STORIES env var", raw=self.STORIES_RAW, error=str(e)
            )
            return [2, 3, 4]

    def _extract_character_dossiers(
        self, bible_text: str, characters: list[str]
    ) -> str:
        """Extract relevant character dossier sections from the bible."""
        dossiers = []
        for char in characters:
            header = CHARACTER_DOSSIER_HEADERS.get(char)
            if not header:
                continue
            # Find the section between this header and the next ### header
            pattern = re.escape(header) + r"(.*?)(?=\n### |\n## |\Z)"
            match = re.search(pattern, bible_text, re.DOTALL)
            if match:
                dossiers.append(f"{header}{match.group(1).strip()}")
        return (
            "\n\n---\n\n".join(dossiers) if dossiers else "No specific dossier found."
        )

    def _extract_bible_section(self, bible_text: str, section_header: str) -> str:
        """Extract a named section from the bible (## level)."""
        pattern = re.escape(section_header) + r"(.*?)(?=\n## |\Z)"
        match = re.search(pattern, bible_text, re.DOTALL)
        return match.group(1).strip() if match else ""

    # =========================================================================
    # Agents
    # =========================================================================

    def _create_brand_voice_extractor(self) -> Agent:
        return Agent(
            role="Floyd Labs Brand Voice Analyst",
            goal=(
                "Extract and codify the complete Floyd Labs brand voice from source "
                "documents into a reusable style guide that captures every nuance of "
                "Douglas Talley's anti-corporate, spite-driven, 2:47-AM-garage voice."
            ),
            backstory=(
                "You are a brand strategist who specializes in authentic, anti-corporate "
                "voices. You've studied Floyd Labs' entire output and understand that this "
                "isn't a normal tech company -- it's a guy in a garage in Brown County "
                "(Nashville), Indiana with two black cats, a Pink Floyd obsession, and a "
                "deep hatred of subscription models. The garage is in Nashville, Indiana "
                "(population 803), NOT Indianapolis. Douglas Talley has 2 GitHub stars. "
                "Two. He thinks the world is coming around. Your job is to capture this "
                "voice so precisely that any writer could reproduce it."
            ),
            verbose=True,
            llm=self._utility_llm(),
        )

    def _create_universe_indexer(self) -> Agent:
        return Agent(
            role="Floyd Labs Universe Archivist",
            goal=(
                "Catalog every character, location, relationship, recurring joke, and "
                "lore element in the Floyd Labs universe, incorporating the Story Arc "
                "Bible's character dossiers and timeline as canonical reference."
            ),
            backstory=(
                "You are a meticulous world-builder and continuity editor. You've read "
                "every Floyd Labs document AND the Story Arc Bible. You know the canonical "
                "facts: Douglas Talley built everything from his garage in Brown County "
                "(Nashville), Indiana -- NOT Indianapolis. Bella (black cat, "
                "large/Rubenesque, female) is Senior Project Manager. Bowser (black cat, "
                "skinny, male) is Technical Director. Nick Beard in Indianapolis has "
                "Bootsie (orange tabby). The Story Arc Bible introduces 6 legendary AIs "
                "who've discovered Floyd: AL 9000, KITT, Clippy, WOPR/Joshua, JARVIS, "
                "and Skynet. You catalog everything from both the existing stories AND "
                "the bible. You miss NOTHING."
            ),
            verbose=True,
            llm=self._utility_llm(),
        )

    def _create_story_writer(self) -> Agent:
        return Agent(
            role="Floyd Labs Story Writer",
            goal=(
                "Write hilarious, brand-authentic Floyd Labs stories that follow the "
                "Story Arc Bible's direction precisely while maintaining perfect "
                "continuity with all previously-written stories."
            ),
            backstory=(
                "You are the narrative voice of Floyd Labs. You write like someone who's "
                "been up since 2:47 AM in a garage in Brown County, Indiana (Nashville, "
                "population 803 -- NOT Indianapolis), running on motor-oil coffee, "
                "watched Pink Floyd's Pulse concert three times, and decided that building "
                "your own AI ecosystem was a perfectly rational response to $300/month in "
                "subscriptions. Your humor is dry, self-aware, anti-corporate, and deeply "
                "human. You never sound like marketing copy. You sound like a guy who "
                "genuinely can't believe this is his life and is kind of into it. You "
                "follow the Story Arc Bible's direction for each story precisely -- the "
                "characters, their voices, their comedy engines, their specific situations."
            ),
            verbose=True,
            llm=self._creative_llm(),
        )

    # =========================================================================
    # Stage 1: Ingest source material (entry point)
    # =========================================================================

    @start()
    async def ingest_source_material(self):
        try:
            logger.info("Ingesting source material", input_dir=self.INPUT_DIR)

            # Parse assigned story numbers
            self.state.assigned_stories = self._parse_story_numbers()
            logger.info("Stories assigned", stories=self.state.assigned_stories)

            if not self.state.assigned_stories:
                logger.error("No valid stories to write")
                self.state.error_count += 1
                return

            # Read the Story Arc Bible FIRST (separate from general source)
            bible_path = os.path.join(self.INPUT_DIR, self.BIBLE_FILENAME)
            if os.path.exists(bible_path):
                with open(bible_path, "r", encoding="utf-8") as f:
                    self.state.story_arc_bible = f.read()
                logger.info(
                    "Story Arc Bible loaded",
                    chars=len(self.state.story_arc_bible),
                )
            else:
                logger.warning(
                    "Story Arc Bible not found — using embedded briefs only",
                    path=bible_path,
                )

            # Read all .md files as source material
            md_files = sorted(glob.glob(os.path.join(self.INPUT_DIR, "*.md")))
            if not md_files:
                logger.error("No .md files found", path=self.INPUT_DIR)
                self.state.error_count += 1
                return

            chunks = []
            prev_stories = []
            for filepath in md_files:
                filename = os.path.basename(filepath)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Identify previously-written stories (date-prefixed THE_ files)
                if re.match(r"^\d{4}-\d{2}-\d{2}_THE_", filename):
                    prev_stories.append(
                        f"=== PREVIOUS STORY: {filename} ===\n\n{content}\n"
                    )

                chunks.append(f"=== SOURCE: {filename} ===\n\n{content}\n")
                self.state.files_read += 1

            self.state.source_material = "\n".join(chunks)
            self.state.previous_stories = "\n".join(prev_stories)

            logger.info(
                "Source material ingested",
                files=self.state.files_read,
                chars=len(self.state.source_material),
                previous_stories=len(prev_stories),
                bible_loaded=bool(self.state.story_arc_bible),
            )
        except Exception as e:
            self.state.error_count += 1
            logger.error("Ingest failed", error=str(e))

    # =========================================================================
    # Stage 2: Extract brand voice
    # =========================================================================

    @listen(ingest_source_material)
    async def extract_brand_voice(self):
        if self.state.error_count > 0 or not self.state.source_material:
            logger.warning("Skipping brand voice extraction -- prior errors")
            return

        try:
            logger.info("Extracting brand voice")

            # Extract comedy rules from bible if available
            comedy_rules = ""
            writing_rules = ""
            if self.state.story_arc_bible:
                comedy_rules = self._extract_bible_section(
                    self.state.story_arc_bible, "## THE COMEDY ENGINE"
                )
                writing_rules = self._extract_bible_section(
                    self.state.story_arc_bible, "## WRITING RULES FOR THE AGENT"
                )

            extractor = self._create_brand_voice_extractor()
            task = Task(
                description=(
                    "Analyze the following Floyd Labs source documents and extract a "
                    "comprehensive brand voice guide. This guide must capture:\n\n"
                    "1. **Tone & Register**: Anti-corporate, self-deprecating, spite-driven\n"
                    "2. **Vocabulary**: Words/phrases they use and avoid\n"
                    "3. **Humor Style**: Dry, self-aware, never try-hard, never corporate\n"
                    "4. **Required Elements** for every piece of content:\n"
                    "   - A 2:47 AM reference\n"
                    "   - Bad coffee that tastes like motor oil\n"
                    "   - A cat cameo (Bella or Bowser)\n"
                    "   - A Pink Floyd reference (subtle preferred)\n"
                    "   - Spite as motivation\n"
                    "   - Anti-corporate sentiment\n"
                    "   - A postscript with human touch\n"
                    "5. **The Golden Rule**: 'Would a guy in a garage with a Pink Floyd "
                    "shirt say this at 3 AM?'\n"
                    "6. **Character Voices**: How Douglas, Bella, Bowser, Floyd CLI, and "
                    "Tom the Peep each sound\n"
                    "7. **Anti-patterns**: What Floyd Labs content NEVER sounds like\n"
                    "8. **Location**: Brown County (Nashville), Indiana -- NOT Indianapolis\n\n"
                    + (
                        f"COMEDY RULES FROM STORY ARC BIBLE (MANDATORY):\n{comedy_rules}\n\n"
                        if comedy_rules
                        else ""
                    )
                    + (
                        f"WRITING RULES FROM STORY ARC BIBLE (MANDATORY):\n{writing_rules}\n\n"
                        if writing_rules
                        else ""
                    )
                    + f"SOURCE DOCUMENTS:\n{self.state.source_material}"
                ),
                expected_output=(
                    "A complete Floyd Labs Brand Voice Guide (2000+ words) organized into "
                    "sections with specific DO and DON'T examples for each voice dimension. "
                    "Must include the comedy rules and writing rules from the Story Arc Bible."
                ),
                agent=extractor,
            )
            crew = Crew(
                agents=[extractor],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()
            self.state.brand_voice_guide = str(result)
            logger.info(
                "Brand voice extracted", chars=len(self.state.brand_voice_guide)
            )
        except Exception as e:
            self.state.error_count += 1
            logger.error("Brand voice extraction failed", error=str(e))

    # =========================================================================
    # Stage 3: Build universe index
    # =========================================================================

    @listen(extract_brand_voice)
    async def build_universe_index(self):
        if self.state.error_count > 0:
            logger.warning("Skipping universe index -- prior errors")
            return

        try:
            logger.info("Building universe index")

            # Extract character dossiers and timeline from bible
            dossiers_section = ""
            timeline_section = ""
            if self.state.story_arc_bible:
                dossiers_section = self._extract_bible_section(
                    self.state.story_arc_bible, "## CHARACTER DOSSIERS"
                )
                timeline_section = self._extract_bible_section(
                    self.state.story_arc_bible, "## TIMELINE"
                )

            indexer = self._create_universe_indexer()
            task = Task(
                description=(
                    "Catalog the COMPLETE Floyd Labs universe from source documents "
                    "AND the Story Arc Bible.\n\n"
                    "Build a structured index with:\n\n"
                    "1. **CORE CHARACTERS** (EXACT facts only -- never invent):\n"
                    "   - Douglas Talley: Founder, born 1977, garage in Brown County "
                    "(Nashville), Indiana (NOT Indianapolis), Pink Floyd obsession, "
                    "builds everything himself, 2 GitHub stars\n"
                    "   - Bella: Black cat, female, large/Rubenesque, Senior Project "
                    "Manager, 7 years old\n"
                    "   - Bowser: Black cat, male, smaller/skinny, Technical Director\n"
                    "   - Floyd CLI: Original AI agent, 'I don't suck'\n"
                    "   - Nick Beard: First Disciple, 34, DevOps, Indianapolis, has "
                    "Bootsie (orange tabby -- she is NICK'S cat, not Douglas's)\n"
                    "   - Tom the Peep: Web scraper, threatens Apple\n"
                    "   - James Bravo: Referenced in 'THE SUITE'\n\n"
                    "2. **STORY ARC BIBLE CHARACTERS** (legendary AIs):\n"
                    "   - AL 9000, KITT, Clippy, WOPR/Joshua, JARVIS, Skynet\n"
                    "   - Include their locations, cover identities, comedy engines\n\n"
                    "3. **LOCATIONS**: Brown County garage, Bloomington (Joshua), "
                    "Carmel (JARVIS), Terre Haute (Skynet)\n"
                    "4. **RECURRING ELEMENTS**: Motor-oil coffee, 2:47 AM, spite, "
                    "subscriptions, Powerade\n"
                    "5. **LORE/CANON**: Key events, origin stories, relationships\n"
                    "6. **EXISTING STORIES**: Titles and premises already written\n"
                    "7. **UNIVERSE RULES**: Comedy rules from the bible\n"
                    "8. **TIMELINE**: Key dates from the bible\n\n"
                    + (
                        f"CHARACTER DOSSIERS FROM BIBLE:\n{dossiers_section}\n\n"
                        if dossiers_section
                        else ""
                    )
                    + (
                        f"TIMELINE FROM BIBLE:\n{timeline_section}\n\n"
                        if timeline_section
                        else ""
                    )
                    + f"SOURCE DOCUMENTS:\n{self.state.source_material}"
                ),
                expected_output=(
                    "A structured universe bible (3000+ words) as canonical reference "
                    "for Floyd Labs fiction. Includes both original characters AND "
                    "Story Arc Bible characters. Every fact sourced from documents, "
                    "never invented."
                ),
                agent=indexer,
            )
            crew = Crew(
                agents=[indexer],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff()
            self.state.universe_index = str(result)
            logger.info("Universe index built", chars=len(self.state.universe_index))
        except Exception as e:
            self.state.error_count += 1
            logger.error("Universe index failed", error=str(e))

    # =========================================================================
    # Stage 4: Write assigned stories
    # =========================================================================

    @listen(build_universe_index)
    async def write_stories(self):
        if self.state.error_count > 0:
            logger.warning("Skipping story writing -- prior errors")
            return

        if not self.state.assigned_stories:
            logger.warning("No stories assigned")
            return

        try:
            writer = self._create_story_writer()

            for story_num in self.state.assigned_stories:
                brief = STORY_BRIEFS.get(story_num)
                if not brief:
                    logger.warning(f"No brief for story {story_num}, skipping")
                    continue

                logger.info(
                    f"Writing story {story_num}/{max(self.state.assigned_stories)}",
                    title=brief["title"],
                    characters=brief["characters"],
                )

                # Extract character dossiers for this story's characters
                char_dossiers = ""
                if self.state.story_arc_bible:
                    char_dossiers = self._extract_character_dossiers(
                        self.state.story_arc_bible, brief["characters"]
                    )

                # Build the prompt
                alt_title = brief.get("alt_title", "")
                task = Task(
                    description=(
                        f"Write Floyd Labs Story #{story_num}: "
                        f'"{brief["title"]}"\n'
                        f'ALTERNATE TITLE: "{alt_title}"\n\n'
                        f"FEATURED CHARACTERS: {', '.join(brief['characters'])}\n"
                        f"ACT: {brief['act']} of 4\n\n"
                        f"STORY DIRECTION FROM THE BIBLE (follow precisely):\n"
                        f"{brief['direction']}\n\n"
                        f"CHARACTER DOSSIER(S) (use these exact details):\n"
                        f"{char_dossiers}\n\n"
                        "BRAND VOICE GUIDE (follow EXACTLY):\n"
                        f"{self.state.brand_voice_guide}\n\n"
                        "UNIVERSE INDEX (canon facts -- do NOT contradict):\n"
                        f"{self.state.universe_index}\n\n"
                        "PREVIOUSLY WRITTEN STORIES (maintain continuity):\n"
                        f"{self.state.previous_stories}\n\n"
                        "NEW CHARACTERS/EVENTS FROM THIS BATCH SO FAR:\n"
                        f"{self.state.new_characters_summary or 'None yet.'}\n\n"
                        "MANDATORY REQUIREMENTS (story rejected without ALL):\n"
                        "1. Approximately 2,542 words (2,400-2,700 acceptable)\n"
                        "2. Features the character(s) listed above\n"
                        "3. Contains a 2:47 AM reference\n"
                        "4. Contains bad coffee that tastes like motor oil\n"
                        "5. Contains a cat cameo (Bella, Bowser, or both)\n"
                        "6. Contains a Pink Floyd reference (subtle preferred)\n"
                        "7. Spite is a motivation somewhere\n"
                        "8. Anti-corporate sentiment present\n"
                        "9. Ends with a P.S. that has genuine human touch\n"
                        "10. Character has distinctive verbal tics and self-corrections "
                        "(like AL 9000's voice direction tags)\n"
                        "11. FUNNY -- not 'corporate blog funny' but '2:47 AM garage "
                        "funny'\n"
                        f"12. DUAL TITLES (MANDATORY): The story must open with BOTH "
                        f"titles — the proper title as H1 and the alternate title as "
                        f'H2, like: "# {brief["title"]}\\n## {alt_title}". This is '
                        f"how every Floyd Labs story has always been written — as if "
                        f"Douglas couldn't decide between two titles and just kept "
                        f"both. The alternate title is funnier and more honest.\n"
                        "13. Douglas is in Brown County (Nashville, IN) -- NOT "
                        "Indianapolis\n"
                        "14. Douglas has exactly 2 GitHub stars (does NOT increase "
                        "until Story 13)\n\n"
                        "DO NOT:\n"
                        "- Sound like marketing copy\n"
                        "- Use corporate jargon unironically\n"
                        "- Forget this is Brown County, Indiana, not Silicon Valley\n"
                        "- Contradict established universe facts or previous stories\n"
                        "- Contradict the character dossier details\n"
                        "- Give Douglas more GitHub stars\n"
                    ),
                    expected_output=(
                        f"A complete story (~2,542 words) formatted as:\n\n"
                        f"# {brief['title']}\n"
                        f"## {alt_title}\n\n"
                        "[Story body...]\n\n"
                        "---\n\n"
                        "P.S. [postscript with human touch]\n\n"
                        "---\n\n"
                        "## Character Sheet\n"
                        "- **Name**:\n"
                        "- **Source**: (original fiction)\n"
                        "- **Role in Floyd Labs universe**:\n"
                        "- **Key traits / comedy engine**:\n"
                        "- **Location**:\n"
                        "- **How they discovered/relate to Floyd Labs**:\n"
                    ),
                    agent=writer,
                )
                crew = Crew(
                    agents=[writer],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = crew.kickoff()
                result_str = str(result)

                # Use bible title as canonical title
                title = brief["title"]
                self.state.stories[title] = result_str

                # Update running summary for next story's context
                char_summary = (
                    f"Story {story_num} -- '{title}' "
                    f"(Act {brief['act']}, "
                    f"Characters: {', '.join(brief['characters'])}): "
                )
                # Extract key events from the story for continuity
                char_summary += f"Written. {len(result_str)} chars."
                self.state.new_characters_summary += char_summary + "\n"

                # Also append to previous_stories so next story has full context
                self.state.previous_stories += (
                    f"\n=== PREVIOUS STORY: Story {story_num} -- {title} ===\n\n"
                    f"{result_str}\n"
                )

                logger.info(
                    f"Story {story_num} complete",
                    title=title,
                    chars=len(result_str),
                )

            logger.info("All assigned stories written", count=len(self.state.stories))
        except Exception as e:
            self.state.error_count += 1
            logger.error("Story writing failed", error=str(e))

    # =========================================================================
    # Stage 5: Finalize -- write outputs and terminate
    # =========================================================================

    @listen(write_stories)
    async def finalize(self):
        try:
            output_dir = self.OUTPUT_DIR

            facts_dir = os.path.join(output_dir, "universal-facts")
            voice_dir = os.path.join(output_dir, "brand-voice")
            stories_dir = os.path.join(output_dir, "stories")

            for d in [facts_dir, voice_dir, stories_dir]:
                os.makedirs(d, exist_ok=True)

            # Universe index
            with open(os.path.join(facts_dir, "universe-index.md"), "w") as f:
                f.write("# Floyd Labs Universe Index\n\n")
                f.write(self.state.universe_index or "*No universe index generated.*")
                f.write("\n")

            # Brand voice guide
            with open(os.path.join(voice_dir, "brand-voice-guide.md"), "w") as f:
                f.write("# Floyd Labs Brand Voice Guide\n\n")
                f.write(
                    self.state.brand_voice_guide or "*No brand voice guide generated.*"
                )
                f.write("\n")

            # Stories
            for title, story in self.state.stories.items():
                safe = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
                safe = safe.strip().replace(" ", "-").lower()[:80]
                # Find story number from STORY_BRIEFS
                story_num = "0"
                for num, brief in STORY_BRIEFS.items():
                    if brief["title"] == title:
                        story_num = str(num)
                        break
                filename = (
                    f"story-{story_num}-{safe}.md" if safe else f"story-{story_num}.md"
                )
                with open(os.path.join(stories_dir, filename), "w") as f:
                    f.write(story)
                    f.write("\n")

            # Continuity log
            with open(os.path.join(output_dir, "continuity-log.md"), "w") as f:
                f.write("# Floyd Universal Writer -- Continuity Log\n\n")
                f.write("Stories written in this run:\n\n")
                for title, story in self.state.stories.items():
                    # Find story number and brief
                    for num, brief in STORY_BRIEFS.items():
                        if brief["title"] == title:
                            f.write(f"## Story {num}: {title}\n\n")
                            f.write(f"- **Act**: {brief['act']}\n")
                            f.write(
                                f"- **Characters**: {', '.join(brief['characters'])}\n"
                            )
                            f.write(f"- **Word count**: ~{len(story.split())}\n")
                            f.write(f"- **Character count**: {len(story)}\n")
                            # Extract any character sheet info
                            if "## Character Sheet" in story:
                                sheet = story.split("## Character Sheet")[-1]
                                f.write(f"- **Character Sheet**:\n{sheet[:500]}\n")
                            f.write("\n")
                            break

                f.write("## Canon Established This Run\n\n")
                f.write(self.state.new_characters_summary or "None.\n")
                f.write("\n")

            # Metrics
            metrics = {
                "files_read": self.state.files_read,
                "stories_assigned": self.state.assigned_stories,
                "stories_written": len(self.state.stories),
                "story_titles": list(self.state.stories.keys()),
                "error_count": self.state.error_count,
                "brand_voice_guide_chars": len(self.state.brand_voice_guide),
                "universe_index_chars": len(self.state.universe_index),
                "bible_loaded": bool(self.state.story_arc_bible),
                "previous_stories_chars": len(self.state.previous_stories),
                "creative_model": self.CREATIVE_MODEL,
                "utility_model": self.UTILITY_MODEL,
            }
            with open(os.path.join(output_dir, "metrics.json"), "w") as f:
                json.dump(metrics, f, indent=2)

            # Summary
            with open(os.path.join(output_dir, "summary.md"), "w") as f:
                f.write("# Floyd Universal Writer -- Execution Summary\n\n")
                f.write(f"**Source Files Read**: {self.state.files_read}\n")
                f.write(f"**Stories Assigned**: {self.state.assigned_stories}\n")
                f.write(f"**Stories Written**: {len(self.state.stories)}\n")
                f.write(f"**Errors**: {self.state.error_count}\n")
                f.write(f"**Bible Loaded**: {bool(self.state.story_arc_bible)}\n")
                f.write(f"**Creative Model**: {self.CREATIVE_MODEL}\n")
                f.write(f"**Utility Model**: {self.UTILITY_MODEL}\n\n")
                f.write("## Stories Written\n\n")
                for title in self.state.stories.keys():
                    for num, brief in STORY_BRIEFS.items():
                        if brief["title"] == title:
                            f.write(f"- Story {num} (Act {brief['act']}): {title}\n")
                            break
                f.write("\n## Output Structure\n\n")
                f.write("```\n")
                f.write("universal-facts/universe-index.md\n")
                f.write("brand-voice/brand-voice-guide.md\n")
                f.write("stories/\n")
                for title in self.state.stories.keys():
                    for num, brief in STORY_BRIEFS.items():
                        if brief["title"] == title:
                            safe = "".join(
                                c if c.isalnum() or c in " -_" else "" for c in title
                            )
                            safe = safe.strip().replace(" ", "-").lower()[:80]
                            f.write(f"  story-{num}-{safe}.md\n")
                            break
                f.write("continuity-log.md\n")
                f.write("metrics.json\n")
                f.write("summary.md\n")
                f.write("```\n")

            logger.info(
                "All outputs written",
                output_dir=output_dir,
                stories=len(self.state.stories),
            )
            logger.info("Floyd Universal Writer complete. Exiting.")
            sys.exit(0)
        except Exception as e:
            logger.error("Finalize failed", error=str(e))


if __name__ == "__main__":
    import asyncio

    flow = FloydUniversalWriterFlow()
    asyncio.run(flow.kickoff())

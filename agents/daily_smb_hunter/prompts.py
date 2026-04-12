"""
================================================================================
            DAILY SMB HUNTER — TASK PROMPTS
================================================================================
"""

from typing import List


def get_scout_task(area: str, industries: List[str], exclusions: List[str]) -> str:
    exclude_text = ""
    if exclusions:
        exclude_text = f"\n\nDO NOT select any of these businesses (already targeted):\n" + "\n".join(f"- {e}" for e in exclusions[-30:])

    return f"""
Find ONE small business in the {area} area that is the best candidate for an AI
automation solution from Legacy AI.

SEARCH AREA: {area} and surrounding neighborhoods
TARGET INDUSTRIES (in priority order): {', '.join(industries[:10])}

WHAT MAKES A GREAT TARGET:
1. Owner-operated or small team (1-15 employees)
2. Service-based business (not retail chain, not franchise HQ)
3. Currently operating and busy (has recent Google reviews)
4. Has a Google Business listing with their info visible
5. Website is weak, outdated, or missing entirely
6. Good Google rating (3.5+) but low review count (<100) — means they're good but invisible
7. Industry where online presence directly drives revenue
8. No obvious existing relationship with a marketing agency or web firm

SEARCH STRATEGY:
- Search Google Maps for businesses in {area}
- Check "plumber near Southport IN", "HVAC Southport Indianapolis", etc.
- Look at Google Business Profiles for owner info, hours, photos
- Visit their website (if they have one) to assess quality
- Check their review count and recency
{exclude_text}

RETURN exactly one business with:
- Business name
- Industry
- Full address
- Phone number
- Email (if findable)
- Website URL (if they have one)
- Google rating and review count
- Owner name (if visible on Google, LinkedIn, or their site)
- Why this business is the perfect target (2-3 sentences)

Pick the BEST one. Not the first one you find.
"""


def get_deep_research_task(business_name: str, industry: str, address: str, website: str) -> str:
    return f"""
Build a complete intelligence package on {business_name}, a {industry} business
at {address}.
Website: {website if website else 'None found'}

RESEARCH CHECKLIST:

1. OWNER PROFILE
   - Full name and title
   - LinkedIn profile
   - Background (how long running this business, previous career)
   - Community involvement, chamber of commerce, local associations
   - Any quotes or interviews in local media

2. BUSINESS PROFILE
   - How long in business (check Google, BBB, state records)
   - Estimated employee count (check Google, LinkedIn, website team page)
   - Estimated annual revenue (based on industry averages for their size/location):
     * Solo tradesperson in Southport: $80-150K
     * 2-5 employee service company: $200-500K
     * 5-15 employee service company: $500K-2M
     * Restaurant with 10-20 seats: $300-600K
     * Restaurant with 20-50 seats: $600K-1.5M
   - Service area (local only? regional?)

3. ONLINE PRESENCE
   - Google Business Profile: rating, review count, photos, posts
   - Website: exists? quality? mobile? last updated?
   - Social media: Facebook, Instagram, TikTok — active?
   - Review sites: Yelp, Angi, HomeAdvisor, Thumbtack
   - Directory listings: BBB, chamber, industry-specific

4. COMPETITIVE LANDSCAPE
   - Name 3-5 direct competitors in the same area
   - How does this business compare online?
   - Who's winning the Google search for "[industry] Southport IN"?

5. PAIN POINTS (infer from evidence)
   - What's clearly costing them money right now?
   - What are customers complaining about in reviews?
   - What are competitors doing that they're not?
   - What simple automation would have immediate impact?

Return a structured intelligence report. Be specific with numbers, names, and links.
"""


def get_solution_design_task(business_intel: str, min_impact: str) -> str:
    return f"""
Based on the following business intelligence, design the exact AI agent solution
that will increase this business's revenue by a MINIMUM of {min_impact} annually.

BUSINESS INTELLIGENCE:
{business_intel}

REQUIREMENTS:
1. The solution must produce a measurable, verifiable revenue impact of {min_impact}+
2. Show your math — how you get to {min_impact} with specific numbers
3. The solution must be achievable with CrewAI agents (web search, scraping,
   email drafting, content generation, data analysis, scheduling)
4. The solution must NOT require the business to change their workflow significantly
5. Results must be visible within 90 days

SOLUTION DESIGN FORMAT:

**Solution Name:** [descriptive name]
**Type:** [single_agent / multi_agent / workflow]
**Revenue Strategy:** [increase_leads / reduce_churn / upsell / cut_costs / improve_conversion]

**How It Works:**
[3-5 bullet points explaining what the agent does in plain English]

**Revenue Math:**
[Show the calculation. Example:]
- Current state: 200 Google reviews, ranking #4 for "plumber Southport"
- Agent action: Automated review solicitation after every job → 15 new reviews/month
- Impact: Move from #4 to #2 in local search within 6 months
- More visibility = ~20% more inbound calls = ~X more jobs/month at $Y average
- Annual impact: $Z (which is N% of estimated revenue)

**Agent Requirements:**
- Tools needed: [SerperDevTool, ScrapeWebsiteTool, etc.]
- Data inputs: [what the agent needs access to]
- Output: [what it produces and where]
- Run frequency: [daily, weekly, on-trigger]

**Pricing Recommendation:**
- Setup: $[amount] (justified by [hours/complexity])
- Monthly: $[amount] (justified by [ongoing value])
- ROI timeline: [when they break even]

Be conservative with projections. Under-promise so Ryan can over-deliver.
"""


def get_agent_build_task(solution_spec: str, business_name: str) -> str:
    agent_name = business_name.lower().replace(" ", "_").replace("'", "")[:30]
    return f"""
Write the complete Python code for a CrewAI agent that implements this solution:

{solution_spec}

TARGET BUSINESS: {business_name}

CODE REQUIREMENTS:
- Follow the Godzilla pattern exactly
- Files needed: state.py, agents.py, prompts.py, flow.py, __init__.py
- State class: Pydantic BaseModel with task_id, status, phase, error_count, progress, confidence
- Flow class: Flow[State] with @start, @listen decorators
- Output directory: /Volumes/SanDisk1Tb/LAIAS_AGENT_OUTPUT/{agent_name}/
- Each run creates timestamped subdirectory with descriptive name
- structlog for logging
- Error recovery with try/except in each phase
- LLM config: use os.environ for PORTKEY_VIRTUAL_KEY and LLM_BASE_URL

OUTPUT FORMAT:
Return each file clearly separated with the filename as a header:

### state.py
```python
[code]
```

### agents.py
```python
[code]
```

### prompts.py
```python
[code]
```

### flow.py
```python
[code]
```

### __init__.py
```python
[code]
```

The code must be copy-paste ready. No placeholders. No TODOs. Production-ready.
"""


def get_sales_package_task(business_intel: str, solution_spec: str, config: dict) -> str:
    return f"""
Create Ryan's complete sales package for this deal.

BUSINESS INTELLIGENCE:
{business_intel}

SOLUTION DESIGNED:
{solution_spec}

RYAN'S PROFILE:
- Non-technical, personable, enthusiastic
- Sells results, never technology
- Best in face-to-face and phone conversations
- Needs materials he can read once and deliver naturally

CREATE THE FOLLOWING:

1. **One-Liner** (under 15 words)
   What Ryan says when someone asks "what do you do?"
   Example: "I help [industry] businesses get more customers without hiring more staff."

2. **Elevator Pitch** (30 seconds, under 80 words)
   For when Ryan meets the owner cold. Reference their specific business.

3. **Discovery Questions** (5 questions)
   Questions Ryan asks to get the owner talking about their pain points.
   These should feel like conversation, not an interview.

4. **Objection Handlers** (top 5)
   - "I can't afford it" → [response]
   - "I'm too busy to deal with this" → [response]
   - "I already have a website/marketing" → [response]
   - "How do I know it works?" → [response]
   - "Let me think about it" → [response]

5. **Voicemail Script** (under 20 seconds when spoken)
   For when Ryan calls and gets voicemail. Must mention their business by name.

6. **Intro Email** (under 150 words)
   Cold email Ryan can send. Must reference specific findings about their business.

7. **Leave-Behind Summary** (one page, printable)
   What Ryan hands the owner after a meeting. Their problems, the solution,
   the pricing, and how to say yes. Include {config.get('company_name', 'Legacy AI')}
   contact info.

8. **Competitive Advantage** (one sentence)
   Why Legacy AI vs doing nothing or hiring a marketing firm.

9. **Urgency Hook** (one sentence)
   Why acting now matters. Must be true, not manufactured.

10. **Closing Line** (one sentence)
    The last thing Ryan says before leaving. Plants the seed.

Write everything in Ryan's voice — warm, direct, zero jargon.
The owner should feel like Ryan actually gives a shit about their business.
"""


def get_ad_copy_task(business_intel: str, solution_spec: str) -> str:
    return f"""
Write targeted ad copy and marketing materials for reaching this specific business owner.

BUSINESS INTELLIGENCE:
{business_intel}

SOLUTION:
{solution_spec}

CREATE:

1. **Cold Email** (subject + body, under 200 words)
   - Subject must be specific enough that they open it
   - Body must reference something real about their business
   - End with one clear call to action

2. **Facebook/Instagram Ad** (if applicable for this industry)
   - Headline (under 10 words)
   - Body (under 100 words)
   - Call to action
   - Targeting notes (location, interests, job titles)

3. **Printable One-Pager** (text content for a leave-behind)
   - Their business name and specific problems identified
   - What we'll do (3 bullet points, no jargon)
   - Pricing (setup + monthly)
   - "Here's what happens next" (3 steps to get started)
   - Contact info for Legacy AI

Every piece must feel like it was written specifically for this one business.
If you could swap in any other business name and it still reads the same, rewrite it.
"""

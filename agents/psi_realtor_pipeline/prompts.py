"""
================================================================================
                PSI REALTOR PIPELINE — TASK PROMPTS
================================================================================
Task descriptions and instructions for each pipeline phase.
================================================================================
"""

from typing import List


def get_research_task(cities: List[str], max_leads: int) -> str:
    """Task prompt for the realtor researcher."""
    city_list = ", ".join(cities)
    return f"""
Research and identify up to {max_leads} active real estate agents in the following
Central Indiana cities: {city_list}.

For each agent found, collect:
1. Full name
2. Email address (required — skip if not findable)
3. Phone number (if available)
4. Brokerage name
5. Primary city/area they serve
6. 1-3 recent listings or transactions (address or neighborhood)
7. Any specialties mentioned (first-time buyers, relocation, investment, etc.)

SEARCH STRATEGY:
- Search for "top real estate agents [city] Indiana 2026"
- Search for "realtor [city] IN residential"
- Check Zillow, Realtor.com, and brokerage websites for agent directories
- Look at recent MLS listings in these cities for listing agents
- Focus on agents with active listings in the last 90 days

PRIORITIZE:
- Agents at mid-size local brokerages (Carpenter, FC Tucker, RE/MAX, Keller Williams)
- Agents handling residential resale (not new construction)
- Agents in suburbs with older housing stock (20+ year old homes have sewer issues)
- Agents with visible contact information

SKIP:
- Agents who only do commercial real estate
- Agents focused exclusively on luxury/new construction
- Agents outside the service area
- Team accounts with no individual contact info

Return a structured list of findings. Each entry must have at minimum:
name, email, brokerage, and city.
"""


def get_qualification_task(leads_data: str) -> str:
    """Task prompt for lead qualification."""
    return f"""
Evaluate the following realtor leads for partnership fit with Precision Sewer Inspection,
a Central Indiana sewer scope company that charges $159/inspection and offers volume
packages for brokerages.

LEADS TO EVALUATE:
{leads_data}

SCORING CRITERIA (rate each 1-5):
1. Transaction Volume: Higher volume agents send more inspection referrals
2. Service Area Match: Do they work in our 12 service cities?
3. Buyer Focus: Buyer agents need inspections; listing agents less so
4. Accessibility: Is their contact info complete and verified?
5. Infrastructure Age: Do they work in areas with older homes (sewer issues)?

QUALIFICATION RULES:
- QUALIFIED (score 15+): Strong fit, proceed with outreach
- MAYBE (score 10-14): Decent fit, include but lower priority
- DISQUALIFIED (score <10): Poor fit, skip

For each lead, provide:
- Score breakdown
- Final status (QUALIFIED / MAYBE / DISQUALIFIED)
- One sentence explaining why

Return the qualified and maybe leads with their scores.
"""


def get_outreach_task(lead_name: str, lead_data: str) -> str:
    """Task prompt for drafting outreach to a specific realtor."""
    return f"""
Write a personalized outreach email from Precision Sewer Inspection to the following realtor:

{lead_data}

EMAIL REQUIREMENTS:
- Subject line: Short, specific, not spammy (reference their city or brokerage)
- From: Douglas Talley, Co-Owner, Precision Sewer Inspection
- Length: Under 150 words
- Tone: Professional, warm, local business owner to local business owner

MUST INCLUDE:
1. A specific reference to something about THIS realtor (their brokerage, city, or a recent listing)
2. What Precision Sewer Inspection does (HD sewer scope inspections)
3. Why realtors partner with us (we're inspectors not contractors — no upselling, 24-hour reports)
4. The price point ($159 standard, volume packages available for brokerages)
5. A soft call to action (reply to learn more, or book a call)

MUST NOT:
- Sound like a mass email or template
- Use marketing buzzwords
- Be longer than 150 words
- Include attachments or complex formatting
- Pressure or create false urgency

Sign off as:
Douglas Talley
Co-Owner, Precision Sewer Inspection
(317) 620-3858
precisionsewerinspections.com

Write ONLY the email (subject + body). No commentary.
"""


def get_followup_task(lead_name: str, original_outreach: str) -> str:
    """Task prompt for drafting a follow-up email."""
    return f"""
Write a follow-up email to {lead_name} who did not respond to our initial outreach.

ORIGINAL EMAIL SENT:
{original_outreach}

FOLLOW-UP REQUIREMENTS:
- Under 80 words
- Reference the previous email briefly ("I reached out last week about...")
- Add ONE new piece of value:
  * "We also offer a free video review service — if your buyer already has inspection
    footage from another company, we'll give an independent second opinion at no charge"
  * OR "50% of the inspections we do reveal issues the homeowner didn't know about —
    having a trusted inspector protects your clients and your reputation"
- End with a simple question ("Would it be worth a quick call?")
- Same signature block as original

Write ONLY the email (subject + body). No commentary.
"""


def get_report_task(pipeline_data: str) -> str:
    """Task prompt for the report compiler."""
    return f"""
Compile a pipeline run report from the following data:

{pipeline_data}

REPORT FORMAT:
## PSI Realtor Pipeline Report
**Run Date:** [date]
**Status:** [complete/partial]

### Summary
- Leads Researched: [N]
- Leads Qualified: [N]
- Outreach Drafted: [N]
- CRM Contacts Created: [N]

### Qualified Leads
| Name | Brokerage | City | Score | Status |
|------|-----------|------|-------|--------|
[table rows]

### Outreach Ready for Review
[List each email subject + first line for Douglas to review before sending]

### Action Items
- [Anything that needs manual attention]

### Next Run Recommendations
- [Suggested cities or strategies for next pipeline run]

Keep it scannable. No fluff.
"""

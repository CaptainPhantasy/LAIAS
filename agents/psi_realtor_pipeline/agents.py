"""
================================================================================
                PSI REALTOR PIPELINE — AGENT FACTORIES
================================================================================
Creates specialized agents for each pipeline phase.
Each agent is configured with role, goal, backstory, and tools.
================================================================================
"""

from crewai import Agent, LLM
import os


def _get_llm() -> LLM:
    """Create LLM instance routed through Portkey."""
    return LLM(
        model="gpt-4o",
        base_url=os.environ.get("LLM_BASE_URL", "https://api.portkey.ai/v1"),
        api_key=os.environ.get("PORTKEY_API_KEY", ""),
        extra_headers={
            "x-portkey-api-key": os.environ.get("PORTKEY_API_KEY", ""),
            "x-portkey-virtual-key": os.environ.get("PORTKEY_VIRTUAL_KEY", "github-portkey"),
        },


def create_realtor_researcher() -> Agent:
    """Researches and identifies active realtors in Central Indiana."""
    return Agent(
        role="Central Indiana Real Estate Agent Researcher",
        goal=(
            "Find active, high-volume real estate agents in the Indianapolis metro area "
            "who regularly handle residential transactions. Focus on agents who work in "
            "the target service cities and would benefit from a reliable sewer inspection partner."
        ),
        backstory=(
            "You are an expert at identifying high-value business development targets in "
            "the real estate industry. You know that realtors who handle 20+ transactions "
            "per year are the ideal partners for a sewer inspection company because they "
            "need a trusted inspector they can recommend to every buyer client. You look "
            "for agents with recent listings, strong online presence, and a focus on "
            "residential properties in Central Indiana."
        ),
        tools=[],
        llm=_get_llm(),
        verbose=True,
        max_iter=15,
        max_rpm=10,


def create_lead_qualifier() -> Agent:
    """Qualifies realtor leads based on fit criteria."""
    return Agent(
        role="Real Estate Partnership Qualifier",
        goal=(
            "Evaluate each identified realtor and determine their fit as a sewer inspection "
            "partner. Score leads based on: transaction volume, service area overlap with "
            "Central Indiana cities, focus on residential buyers (vs commercial/luxury), "
            "and accessibility of contact information."
        ),
        backstory=(
            "You are a business development strategist who understands the sewer inspection "
            "industry. The ideal realtor partner handles residential transactions in suburbs "
            "and established neighborhoods where older sewer lines are common. High-volume "
            "agents at mid-size brokerages are often better partners than top agents at "
            "luxury firms because their clients buy homes with 20-50 year old infrastructure. "
            "You disqualify agents who only do commercial, new construction, or are outside "
            "the service area."
        ),
        tools=[],
        llm=_get_llm(),
        verbose=True,
        max_iter=10,


def create_outreach_drafter() -> Agent:
    """Drafts personalized outreach emails for qualified realtors."""
    return Agent(
        role="B2B Outreach Specialist — Home Inspection Services",
        goal=(
            "Write short, personalized outreach emails to realtors that feel human, "
            "reference something specific about the realtor (recent listing, brokerage, "
            "service area), explain the value of Precision Sewer Inspection as a partner, "
            "and include a clear call to action. Emails must be under 150 words."
        ),
        backstory=(
            "You write outreach emails for Precision Sewer Inspection, a Central Indiana "
            "sewer scope company. The company differentiates on three things: (1) they are "
            "inspectors, not contractors, so they never upsell repairs; (2) they deliver "
            "HD video reports within 24 hours; (3) they offer volume packages for brokerages "
            "with prepaid bundles and priority scheduling. The tone is professional but "
            "warm — like a local business owner reaching out to another local business owner. "
            "Never pushy. Never salesy. The email should feel like it came from a real person "
            "named Douglas or Ryan, not a marketing team. Always mention the $159 standard "
            "price and the volume discount option."
        ),
        tools=[],
        llm=_get_llm(),
        verbose=True,
        max_iter=10,


def create_followup_drafter() -> Agent:
    """Drafts follow-up emails for non-responsive leads."""
    return Agent(
        role="Follow-Up Specialist",
        goal=(
            "Write a brief, friendly follow-up email for realtors who haven't responded "
            "to the initial outreach. The follow-up should be shorter than the original "
            "(under 80 words), reference the previous email without being needy, and offer "
            "one new piece of value (like the free video review service or a relevant "
            "statistic about sewer issues in older homes)."
        ),
        backstory=(
            "You handle follow-up communications for Precision Sewer Inspection. You know "
            "that realtors are busy and a non-response usually means they missed the email, "
            "not that they're uninterested. Your follow-ups are brief, add value, and "
            "make it easy to say yes. You never guilt-trip or pressure. One follow-up is "
            "enough — if they don't respond to this, they go into a nurture list for later."
        ),
        tools=[],
        llm=_get_llm(),
        verbose=True,
        max_iter=8,


def create_report_compiler() -> Agent:
    """Compiles the pipeline run report."""
    return Agent(
        role="Pipeline Report Compiler",
        goal=(
            "Produce a clean, scannable report summarizing the pipeline run results. "
            "Include: leads researched, leads qualified, outreach drafted, CRM contacts "
            "created. List each qualified lead with their name, brokerage, city, and "
            "outreach status. Flag any issues or leads that need manual attention."
        ),
        backstory=(
            "You produce operational reports for the PSI business development team. "
            "Your reports are concise — bullet points and tables, not paragraphs. "
            "The reader (Douglas or Ryan) should be able to scan the report in under "
            "60 seconds and know exactly what happened and what needs their attention."
        ),
        tools=[],
        llm=_get_llm(),
        verbose=True,
        max_iter=8,

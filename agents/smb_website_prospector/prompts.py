"""
================================================================================
            SMB WEBSITE PROSPECTOR — TASK PROMPTS
================================================================================
"""

from typing import List


def get_discovery_task(cities: List[str], industries: List[str], max_prospects: int) -> str:
    city_list = ", ".join(cities)
    industry_list = ", ".join(industries)
    return f"""
Find up to {max_prospects} small service businesses with websites in these Indiana towns:
{city_list}

Target these industries: {industry_list}

For each business, collect:
1. Business name
2. Website URL (must be a real website, not just a Facebook page or Yelp listing)
3. Contact email (check Contact page, footer, About page)
4. Phone number
5. Industry/trade
6. City

SEARCH STRATEGY:
- Search "[industry] [city] Indiana" for each combination
- Visit the top results that are actual business websites
- Check Google Maps listings for businesses with website links
- Prioritize businesses that clearly built or paid for a website (even if it's bad)

SKIP:
- Businesses with no website (Google listing only)
- Businesses with only a Facebook page
- National chains or franchises
- Businesses with clearly professional, modern websites (they don't need help)
- Businesses with no findable email address

PRIORITIZE:
- Sites that look dated, broken on mobile, or have obvious issues
- Owner-operated businesses (not corporate)
- Businesses in industries where online presence directly drives revenue
- Sites built on free website builders (Wix free tier, GoDaddy basic, etc.)

Return a structured list. Each entry must have: business_name, website_url, email, phone, industry, city.
"""


def get_analysis_task(business_name: str, website_url: str) -> str:
    return f"""
Analyze the website for {business_name} at {website_url}.

Evaluate these categories and find specific issues:

1. **SEO** (Can Google find them?)
   - Page title and meta description present and relevant?
   - Heading structure (H1, H2) logical?
   - Local SEO signals (city name, service area mentioned)?
   - Google Business Profile linked?

2. **Mobile** (Does it work on a phone?)
   - Responsive design or fixed-width?
   - Touch targets sized properly?
   - Text readable without zooming?
   - Phone number clickable?

3. **Performance** (Does it load fast?)
   - Obvious heavy images or slow elements?
   - Excessive scripts or widgets?

4. **Security** (Is it trustworthy?)
   - HTTPS enabled?
   - SSL certificate valid?

5. **Content** (Does it sell their service?)
   - Clear description of what they do?
   - Service area mentioned?
   - Pricing or "get a quote" flow?
   - Customer reviews or testimonials?
   - Unique content or template text?

6. **Contact/Conversion** (Can a customer reach them?)
   - Contact form working?
   - Phone number prominent and clickable?
   - Email visible?
   - Hours of operation listed?
   - Call to action clear?

For each issue found, provide:
- Category (SEO/Mobile/Performance/Security/Content/Contact)
- Severity (critical/high/medium/low)
- What's wrong (one sentence)
- How to fix it (one sentence)

Score the site 0-100 where:
- 0-30: Major problems, losing significant business
- 31-50: Below average, multiple issues costing money
- 51-70: Decent but has room for improvement
- 71-85: Good, minor improvements possible
- 86-100: Excellent, professional quality

Be honest but constructive. The business owner will read this.
"""


def get_outreach_email_task(
    business_name: str,
    owner_email: str,
    city: str,
    industry: str,
    site_score: int,
    top_issues: str,
    config: dict,
) -> str:
    return f"""
Write an outreach email to {business_name} in {city}, Indiana.
They are a {industry} business.
Their website scored {site_score}/100 in our analysis.

TOP ISSUES FOUND:
{top_issues}

EMAIL STRUCTURE:

1. **Opening** (2 sentences max)
   - Introduce yourself as Douglas Talley, a local web developer
   - Mention you came across their website while researching {industry} businesses in {city}

2. **The Value** (3-4 sentences)
   - Summarize 2-3 of their biggest website issues in plain English
   - Frame each as money they're losing ("Your site isn't showing up on Google for
     '{industry} {city}' which means customers searching for you are finding your competitors")
   - Don't be mean about their site. Be matter-of-fact.

3. **The Offer** (3 tiers, bulleted)
   - **Option 1 — DIY Report ({config['diy_report_price']})**: "I'll put together a detailed
     report with exact step-by-step instructions your web person can follow to fix these issues.
     Hand it off and you're done."
   - **Option 2 — I'll Handle It ({config['done_for_you_price']})**: "I'll fix the critical
     issues myself. Your site will be mobile-friendly, show up on Google, and actually convert
     visitors into calls. Done in a week."
   - **Option 3 — Ongoing Partnership ({config['monthly_retainer']})**: "{config['retainer_hours']}
     of maintenance, updates, and improvements each month. Plus I'm a phone call away when
     you're ready for something bigger."

4. **The Close** (2 sentences)
   - "If you had the right website person, you'd already know about these issues. I'm here
     when you're ready."
   - "Reply to this email or call me at {config['sender_phone']}."

5. **Signature**
   Douglas Talley
   {config['sender_title']}, {config['sender_company']}
   {config['sender_phone']}
   {config['sender_website']}

RULES:
- Total email under 250 words
- No attachments mentioned (the report comes after they respond)
- Never insult their current site — frame everything as opportunity
- Sound like a real person, not a marketing department
- Reference their specific city and industry
- The line "If you had the right website person, this entire interaction wouldn't be
  happening" should be worked in naturally — it's the closer

Write ONLY the email (subject + body). No commentary.
"""


def get_pipeline_report_task(pipeline_data: str) -> str:
    return f"""
Compile a prospecting pipeline report from this data:

{pipeline_data}

FORMAT:
## SMB Website Prospector Report
**Run Date:** [date]

### Summary
- Businesses Discovered: [N]
- Sites Analyzed: [N]
- Outreach Drafted: [N]

### Top Opportunities (ranked by worst site score = biggest opportunity)
| Business | City | Industry | Score | Critical Issues | Email |
|----------|------|----------|-------|-----------------|-------|
[rows sorted by score ascending]

### Outreach Queue
[For each drafted email: business name, subject line, first sentence preview]

### Market Observations
[1-3 bullet observations about what you noticed across these sites — common issues,
underserved industries, cities with weak web presence]

### Next Run Suggestions
[Which cities/industries to target next based on what was found]

Keep it scannable. Douglas reads this on his phone.
"""

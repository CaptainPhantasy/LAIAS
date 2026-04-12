"""
================================================================================
            SOCIAL MEDIA OPERATOR — TASK PROMPTS
================================================================================
"""

from typing import List


def get_content_strategy_task(topics: List[str], never: List[str], posts_count: int) -> str:
    topics_text = "\n".join(f"- {t}" for t in topics)
    never_text = "\n".join(f"- {t}" for t in never)
    return f"""
Create {posts_count} content ideas for Douglas Talley's social media this week.
Each idea should be one core concept that can be adapted across platforms.

TOPICS TO DRAW FROM:
{topics_text}

NEVER DO:
{never_text}

FOR EACH CONTENT IDEA PROVIDE:
1. **Theme** (2-4 words)
2. **Core Message** (one sentence — what is the takeaway?)
3. **Content Type**: One of: thought_leadership, case_study, behind_the_scenes,
   industry_insight, client_win, tool_demo, hot_take, engagement_hook
4. **Hook** (the first line that makes someone stop scrolling)
5. **Body** (the core content, 2-4 sentences)
6. **Call to Action** (what should the reader do — reply, DM, visit site, think differently?)

VOICE RULES:
- Write as Douglas, first person
- Direct. No filler. No "In today's rapidly evolving landscape..."
- Specific over general. "I built a sewer inspection platform in 20 hours"
  beats "AI is transforming businesses"
- Technical details are okay — his audience respects competence
- Occasional profanity is fine if it is natural
- Stories > opinions > platitudes

MIX IT UP:
- At least 1 case study (PSI, a client win, or something he built)
- At least 1 hot take or industry insight
- At least 1 engagement hook (question, poll, or controversial opinion)
- No more than 1 promotional post (and even that should lead with value)

Return {posts_count} content ideas, clearly numbered.
"""


def get_platform_adapt_task(content_idea: str) -> str:
    return f"""
Adapt this content idea for ALL FIVE platforms. Each version must feel native
to the platform — not a copy-paste.

ORIGINAL IDEA:
{content_idea}

PLATFORM REQUIREMENTS:

**Twitter/X** (max 280 characters)
- Punchy. One idea per tweet.
- Hot takes work. Questions work. Threads for longer content.
- 0-2 hashtags max. No hashtag walls.
- No emojis unless they add meaning.

**LinkedIn** (max 1300 characters)
- Professional storytelling. Start with a hook line.
- Break into short paragraphs (1-2 sentences each).
- End with a question or insight.
- 3-5 relevant hashtags at the bottom.
- First person, conversational but professional.

**Instagram** (caption, max 2200 characters)
- More personal, behind-the-scenes feel.
- Pair with a description of what image/screenshot would go with it.
- 10-15 hashtags at the end (mix of niche and broad).
- Conversational, like talking to a friend.

**Facebook** (max 500 characters for best engagement)
- Community-oriented. Ask questions.
- Share stories that invite comments.
- Casual, warm, local-business friendly.
- 0-2 hashtags.

**TikTok** (script for 30-60 second video)
- Hook in the first 3 seconds (start with the most surprising thing).
- Teach something or share a real result.
- End with a question or call to action.
- Write as a speaking script, not a caption.
- Note what should be on screen.

For each platform, return:
- Platform name
- The adapted post text
- Hashtags (if applicable)
- Notes (image suggestion, thread structure, etc.)
"""


def get_prospecting_task(platforms: List[str], industries: List[str], location: str) -> str:
    platforms_text = ", ".join(platforms)
    industries_text = ", ".join(industries)
    return f"""
Find 5-10 social media signals from local business owners who might need
Legacy AI's services. These are people showing signs they need help with
their website, online marketing, scheduling, reviews, or operations.

SEARCH PLATFORMS: {platforms_text}
TARGET INDUSTRIES: {industries_text}
GEOGRAPHIC FOCUS: {location}

SIGNAL TYPES TO LOOK FOR:
1. Business owner asking for website help or web developer recommendations
2. Complaints about marketing agencies not delivering results
3. Posts about business challenges that automation could solve
4. Service businesses bragging about being busy but clearly overwhelmed
5. Business owners commenting on AI posts with curiosity or skepticism
6. Local businesses with active social accounts but terrible websites
7. Realtors discussing inspection or closing process pain points
8. Any small business owner expressing frustration with technology

FOR EACH PROSPECT FOUND:
- Name (or business name)
- Platform where you found them
- What they said or did (the signal)
- Their business type and approximate location
- Suggested engagement approach (how Douglas should respond — NOT a sales pitch,
  but genuine value-add engagement)
  Example: "Reply to their question about web designers with: 'I built
  precisionsewerinspections.com in about 20 hours for a local company. Happy to
  share what stack I used if you are evaluating options.'"

RULES:
- Never suggest cold DMs to strangers
- Never suggest automated comments or engagement pods
- Every suggested action should provide genuine value first
- The goal is to start a conversation, not close a sale
- Quality over quantity — 3 great signals beat 10 weak ones
"""

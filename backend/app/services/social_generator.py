from app.services.mistral_client import generate_json


def _build_context(opportunity=None, event=None) -> str:
    if opportunity:
        return (
            f"Title: {opportunity.title}\n"
            f"Organization: {opportunity.organization or 'N/A'}\n"
            f"Deadline: {opportunity.deadline or 'Rolling/No fixed deadline'}\n"
            f"Description: {opportunity.description or ''}\n"
            f"Application Link: {opportunity.url}\n"
        )
    if event:
        link_line = event.rsvp_link if event.rsvp_link else "NO_LINK_PROVIDED"
        return (
            f"Title: {event.title}\n"
            f"Date: {event.event_date or 'TBD'}\n"
            f"Time: {event.time_display or 'TBD'}\n"
            f"Location: {event.location or 'TBD'}\n"
            f"Description: {event.description or ''}\n"
            f"RSVP Link: {link_line}\n"
        )
    return ""


def generate_circlein_post(opportunity=None, event=None) -> dict:
    context = _build_context(opportunity, event)

    prompt = f"""You are drafting a CircleIn post for the Cybersecurity & AI Club (CYAI) at York College, CUNY, in the exact voice and structure the club president actually uses.

Match this EXACT structure and tone, based on real examples of how she writes:
1. Start with a short, clear TITLE line summarizing the post (e.g., "CYAI: April Monthly Meeting Reminder" or "Picture Your Success: Headshot Session | This Thursday April 16th!")
2. Then a new line: "Dear Club Members,"
3. Then the body - informational and professional in tone, NOT hype-driven or heavy with emojis. State the real details plainly and clearly (date, time, location if applicable). Emojis are OPTIONAL and used sparingly and functionally (e.g., a single calendar or pin marker), never forced or decorative.
4. The deadline (if any) and the application/RSVP link MUST be wrapped in <strong> tags so they stand out as bolded.
5. If there's an image/flyer that would normally accompany this post, end with a line: "[Attach event flyer/graphic here]" - otherwise omit this line.
6. If the link value is literally "N/A" or "NO_LINK_PROVIDED", DO NOT include any link or URL in the post at all - do not invent, guess, or fabricate a URL under any circumstances. Only include a link if a real one was explicitly given below.

Here is the opportunity/event data:
{context}

Respond with ONLY a JSON object in this exact format, no other text:
{{
  "content": "the full CircleIn post text, following the structure above exactly, using <strong> tags only around the deadline and link (if a real link exists)"
}}
"""

    result = generate_json(prompt)
    if isinstance(result, list) and len(result) > 0:
        result = result[0]
    if not isinstance(result, dict):
        return {"content": ""}
    return result


def generate_instagram_post(opportunity=None, event=None) -> dict:
    context = _build_context(opportunity, event)

    prompt = f"""You are drafting an Instagram caption for the Cybersecurity & AI Club (CYAI) at York College, CUNY (@CYAIYORK), in the same informational, professional-but-warm voice the club uses elsewhere (not overly casual or emoji-heavy marketing copy).

Structure:
1. A short, engaging caption (2-4 sentences) covering the key details - what it is, when/deadline, why it matters for members
2. The deadline or date/time should be clearly stated
3. A call to action - only reference a specific link if a real one was provided below; otherwise say something like "Details in our next newsletter" or "DM us for details" instead of inventing a URL
4. End the caption with a line of relevant hashtags (5-10 hashtags, mixing club-specific like #CYAIYork #YorkCollege with topic-specific like #Cybersecurity #AI #TechInternship #CTF as relevant to the content)
5. If the link value is literally "N/A" or "NO_LINK_PROVIDED", DO NOT mention or invent any URL.

Here is the opportunity/event data:
{context}

Respond with ONLY a JSON object in this exact format, no other text:
{{
  "caption": "the caption text, NOT including the hashtags",
  "hashtags": "the hashtags only, space separated, each starting with #"
}}
"""

    result = generate_json(prompt)
    if isinstance(result, list) and len(result) > 0:
        result = result[0]
    if not isinstance(result, dict):
        return {"caption": "", "hashtags": ""}
    return result

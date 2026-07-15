from datetime import date

from dateutil import parser as date_parser

from app.services.mistral_client import generate_json
from app.services.link_validator import is_safe_url

MAX_ITEMS_PER_CATEGORY = 5


def _parse_deadline(deadline_str: str):
    if not deadline_str:
        return None
    lowered = deadline_str.strip().lower()
    if lowered in ("none", "null", "rolling", "n/a", "rolling/no fixed deadline"):
        return None
    try:
        parsed = date_parser.parse(deadline_str, fuzzy=True)
        return parsed.date()
    except (ValueError, OverflowError):
        return None


def _extract_location(eligibility_str: str):
    if not eligibility_str:
        return None
    if eligibility_str.lower().startswith("location:"):
        return eligibility_str.split(":", 1)[1].strip()
    return None


def _filter_and_sort(items: list, today: date, exclude_ids: set) -> list:
    with_deadline = []
    rolling = []

    for item in items:
        if getattr(item, "link_status", None) == "dead":
            continue

        parsed = _parse_deadline(item.deadline)
        if item.deadline and parsed is None:
            candidate = ("rolling", item)
        elif parsed is None:
            candidate = ("rolling", item)
        elif parsed < today:
            continue
        else:
            candidate = ("dated", (parsed, item))

        if candidate[0] == "rolling":
            rolling.append(item)
        else:
            with_deadline.append(candidate[1])

    with_deadline.sort(key=lambda x: x[0])
    ordered_all = [item for _, item in with_deadline] + rolling

    fresh = [item for item in ordered_all if item.id not in exclude_ids]
    repeats = [item for item in ordered_all if item.id in exclude_ids]

    final = (fresh + repeats)[:MAX_ITEMS_PER_CATEGORY]
    return final


def _filter_events(events: list, today: date) -> list:
    with_date = []
    undated = []

    for event in events:
        parsed = _parse_deadline(event.event_date)
        if parsed is None:
            undated.append(event)
            continue
        if parsed < today:
            continue
        with_date.append((parsed, event))

    with_date.sort(key=lambda x: x[0])
    ordered = [event for _, event in with_date] + undated

    return ordered


def generate_newsletter_html(opportunities: list, month_label: str, events: list = None, recently_featured_ids: set = None) -> dict:
    today = date.today()
    events = events or []
    recently_featured_ids = recently_featured_ids or set()

    grouped = {}
    for opp in opportunities:
        grouped.setdefault(opp.category, []).append(opp)

    filtered_grouped = {
        category: _filter_and_sort(items, today, recently_featured_ids)
        for category, items in grouped.items()
    }
    filtered_grouped = {k: v for k, v in filtered_grouped.items() if v}

    included_opportunity_ids = [
        item.id for items in filtered_grouped.values() for item in items
    ]

    filtered_events = _filter_events(events, today)

    events_text = ""
    if filtered_events:
        events_text = "\n\nUpcoming Club Events:\n"
        for event in filtered_events:
            rsvp = event.rsvp_link if is_safe_url(event.rsvp_link) else "N/A"
            events_text += (
                f"- Title: {event.title}\n"
                f"  Date: {event.event_date or 'TBD'}\n"
                f"  Time: {event.time_display or 'TBD'}\n"
                f"  Location: {event.location or 'TBD'}\n"
                f"  RSVP Link: {rsvp}\n"
                f"  Description: {(event.description or '')[:300]}\n"
            )

    sections_text = ""
    for category, items in filtered_grouped.items():
        sections_text += f"\n\nCategory: {category}\n"
        for item in items:
            location = _extract_location(item.eligibility)
            eligibility_display = item.eligibility if not location else "See posting for full eligibility details"
            safe_url = item.url if is_safe_url(item.url) else "LINK_UNAVAILABLE"

            sections_text += (
                f"- Title: {item.title}\n"
                f"  Organization: {item.organization or 'N/A'}\n"
                f"  Deadline: {item.deadline or 'Rolling/No fixed deadline'}\n"
                f"  Location: {location or 'Not specified / remote-friendly'}\n"
                f"  Application Link: {safe_url}\n"
                f"  Eligibility: {eligibility_display or 'See posting for details'}\n"
                f"  Description: {(item.description or '')[:300]}\n"
            )

    prompt = f"""You are drafting the {month_label} newsletter for the Cybersecurity & AI Club (CYAI) at York College, CUNY.

Match this exact tone, structure, and formatting pattern, based on the club's actual past newsletters:

- Opens with "Dear Club Members," followed by a warm, semester-aware paragraph (2-4 sentences) that reflects on the current point in the semester/summer and previews what's in the newsletter, in an encouraging, community-oriented voice
- If "Upcoming Club Events" data is provided below, include an "Upcoming Events" section FIRST, before any opportunity categories - use <h2>Upcoming Events</h2>, and for each event include: bold title, Date, Time, Location (only if provided), a brief description, and an RSVP/registration link ONLY if the RSVP Link value is a real URL (not "N/A")
- Then sections organized by opportunity category (Scholarships, Internships, Jobs, Fellowships, Bootcamps, CTFs/Competitions) - only include categories that have items below, use <h2> for section headers
- CRITICAL FORMATTING REQUIREMENT for opportunity items - every single item MUST include ALL of these fields, each on its own line, in this exact order:
  1. Bold title (<strong>)
  2. Organization
  3. Deadline (write "Deadline: [date]" or "Deadline: Rolling/No fixed deadline" if none)
  4. Location (write "Location: [location]" only if a real location was provided - OMIT this line entirely if location is "Not specified / remote-friendly")
  5. A 1-2 sentence description of the opportunity
  6. Eligibility Requirements: (a short bullet or sentence)
  7. If the Application Link value is "LINK_UNAVAILABLE", do NOT include any link for this item - just end the item without a link. Otherwise, include a clearly clickable link, formatted as: <a href="[url]">Apply Here</a> for jobs/internships, <a href="[url]">Apply Now</a> for scholarships, or <a href="[url]">Register / Learn More</a> for CTFs/events
- NEVER invent, guess, or fabricate a URL under any circumstances - only use links exactly as provided above
- Closes with a "Stay Connected" section mentioning Instagram @CYAIYORK
- Signs off as: "Best Regards,\\nMaheen Bilal\\nPresident, Cybersecurity and AI Club\\nYork College, CUNY"
- Warm, encouraging, professional but approachable tone, career-readiness framing, matching a real club president's voice

{events_text}

Here is the current opportunity data to include (already filtered to only current/upcoming items with valid links, capped to the most relevant per category, prioritizing items not recently featured):
{sections_text}

Respond with ONLY a JSON object in this exact format, no other text:
{{
  "subject": "a compelling email subject line",
  "html_content": "the full newsletter as clean HTML with basic tags like <p>, <h2>, <ul>, <li>, <a href='...'>, <strong>, <em> - no CSS styling needed, just semantic structure"
}}
"""

    result = generate_json(prompt)

    if isinstance(result, list) and len(result) > 0:
        result = result[0]

    if not isinstance(result, dict):
        result = {"subject": f"CYAI {month_label} Newsletter", "html_content": "<p>Error generating content.</p>"}

    result["included_opportunity_ids"] = included_opportunity_ids
    return result

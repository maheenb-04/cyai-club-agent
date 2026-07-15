from datetime import date, datetime

from dateutil import parser as date_parser

from app.services.mistral_client import generate_json

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


def _filter_and_sort(items: list, today: date) -> list:
    with_deadline = []
    rolling = []

    for item in items:
        parsed = _parse_deadline(item.deadline)
        if item.deadline and parsed is None:
            rolling.append(item)
            continue
        if parsed is None:
            rolling.append(item)
            continue
        if parsed < today:
            continue
        with_deadline.append((parsed, item))

    with_deadline.sort(key=lambda x: x[0])
    ordered = [item for _, item in with_deadline] + rolling

    return ordered[:MAX_ITEMS_PER_CATEGORY]


def generate_newsletter_html(opportunities: list, month_label: str) -> dict:
    today = date.today()

    grouped = {}
    for opp in opportunities:
        grouped.setdefault(opp.category, []).append(opp)

    filtered_grouped = {
        category: _filter_and_sort(items, today)
        for category, items in grouped.items()
    }
    filtered_grouped = {k: v for k, v in filtered_grouped.items() if v}

    sections_text = ""
    for category, items in filtered_grouped.items():
        sections_text += f"\n\nCategory: {category}\n"
        for item in items:
            sections_text += (
                f"- Title: {item.title}\n"
                f"  Organization: {item.organization or 'N/A'}\n"
                f"  Deadline: {item.deadline or 'Rolling/No fixed deadline'}\n"
                f"  URL: {item.url}\n"
                f"  Eligibility: {item.eligibility or 'See posting for details'}\n"
                f"  Description: {(item.description or '')[:300]}\n"
            )

    prompt = f"""You are drafting the {month_label} newsletter for the Cybersecurity & AI Club (CYAI) at York College, CUNY.

Match this exact tone and structure, based on the club's past newsletters:
- Opens with "Dear Club Members," followed by a warm, semester-aware paragraph
- Sections organized by category (Scholarships, Internships, Jobs, Fellowships, Bootcamps, CTFs/Competitions) - only include categories that have items below
- Each item listed with title, organization, deadline, and a brief description, followed by an "Eligibility Requirements:" line
- Closes with a "Stay Connected" section mentioning Instagram @CYAIYORK
- Signs off as: "Best Regards,\\nMaheen Bilal\\nPresident, Cybersecurity and AI Club\\nYork College, CUNY"
- Warm, encouraging, professional but approachable tone, career-readiness framing

Here is the current opportunity data to include (already filtered to only current/upcoming items, capped to the most relevant per category):
{sections_text}

Respond with ONLY a JSON object in this exact format, no other text:
{{
  "subject": "a compelling email subject line",
  "html_content": "the full newsletter as clean HTML with basic tags like <p>, <h2>, <ul>, <li>, <a href='...'>, <strong> - no CSS styling needed, just semantic structure"
}}
"""

    result = generate_json(prompt)

    if isinstance(result, list) and len(result) > 0:
        result = result[0]

    if not isinstance(result, dict):
        return {"subject": f"CYAI {month_label} Newsletter", "html_content": "<p>Error generating content.</p>"}

    return result
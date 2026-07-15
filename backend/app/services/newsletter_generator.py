from app.services.mistral_client import generate_json


def generate_newsletter_html(opportunities: list, month_label: str) -> dict:
    grouped = {}
    for opp in opportunities:
        grouped.setdefault(opp.category, []).append(opp)

    sections_text = ""
    for category, items in grouped.items():
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

Here is the current opportunity data to include:
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
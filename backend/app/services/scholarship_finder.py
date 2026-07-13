import re
from datetime import datetime

from app.services.tavily_client import search_web
from app.services.mistral_client import generate_json
from app.services.link_validator import is_link_valid

AGGREGATOR_DOMAINS = [
    "scholarships360.org",
    "scholarshipsandgrants.us",
    "bigfuture.collegeboard.org",
    "cappex.com",
    "fastweb.com",
    "scholarshipowl.com",
    "unigo.com",
    "niche.com",
    "chegg.com",
    "hbcuconnect.com",
]

STALE_YEAR_PATTERN = re.compile(r"20(1[0-9]|2[0-5])\b")

MONTH_TO_NUM = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def _is_aggregator(url: str) -> bool:
    return any(domain in url for domain in AGGREGATOR_DOMAINS)


def _mentions_stale_year(text: str) -> bool:
    return bool(STALE_YEAR_PATTERN.search(text))


def _deadline_is_valid(deadline_str: str, target_month: str, current_year: int = 2026) -> bool:
    if not deadline_str or deadline_str.lower() in ("none", "null", "rolling", "n/a"):
        return True

    target_month_num = MONTH_TO_NUM.get(target_month.strip().lower())
    if not target_month_num:
        return True

    lowered = deadline_str.lower()
    for month_name, month_num in MONTH_TO_NUM.items():
        if month_name in lowered:
            year_match = re.search(r"20\d{2}", deadline_str)
            deadline_year = int(year_match.group()) if year_match else current_year
            if deadline_year > current_year:
                return True
            if deadline_year == current_year and month_num >= target_month_num:
                return True
            return False

    return True


def _find_official_url(title: str, organization: str) -> str:
    query = f"{title} {organization} 2026 official apply application scholarship"
    results = search_web(query, max_results=6)

    candidates = [r for r in results if not _is_aggregator(r["url"])]
    if not candidates:
        return ""

    candidate_text = "\n".join(
        f"{i}. URL: {c['url']}\n   Title: {c['title']}\n   Snippet: {c['content'][:200]}"
        for i, c in enumerate(candidates)
    )

    prompt = f"""I'm looking for the OFFICIAL, CURRENT (2026) application page for this scholarship:
Title: {title}
Organization: {organization}

Here are search result candidates:
{candidate_text}

Pick the ONE candidate that is most likely the official, current 2026 application page.
Avoid any result that clearly references an old cycle (e.g. 2022, 2023, 2024, 2025 in the title/snippet) unless it's the only option.
Respond with ONLY a JSON array with one object: [{{"index": <number>}}]
If none seem appropriate, respond with: [{{"index": -1}}]
"""

    choice = generate_json(prompt)
    if not choice or not isinstance(choice, list):
        return candidates[0]["url"]

    index = choice[0].get("index", -1)
    if index == -1 or index >= len(candidates):
        return candidates[0]["url"]

    return candidates[index]["url"]


def find_scholarships(target_month: str, max_results: int = 8) -> list[dict]:
    target_month = target_month.strip()

    search_results = search_web(
        f"cybersecurity artificial intelligence scholarship fellowship "
        f"undergraduate college students open application {target_month} 2026",
        max_results=max_results,
    )

    if not search_results:
        return []

    context = "\n\n".join(
        f"Source: {r['url']}\nTitle: {r['title']}\nContent: {r['content'][:1000]}"
        for r in search_results
    )

    prompt = f"""You are helping a college cybersecurity/AI club find CURRENT, OPEN scholarships and fellowships for undergraduate students.

Below are real web search results. Extract ONLY scholarships/fellowships that:
1. Are genuinely open for applications through at least {target_month} 2026 (not expired, not a past cycle like 2022-2025)
2. Are open to undergraduate students nationally, remotely, or in NYC (do NOT include location-restricted programs)
3. Are relevant to cybersecurity, AI, computer science, or related tech fields
4. Are a SPECIFIC named scholarship/fellowship program (not a general listing article)

Search results:
{context}

Respond with ONLY a JSON array, no other text, in this exact format:
[
  {{
    "title": "...",
    "organization": "...",
    "description": "...",
    "deadline": "... or null if rolling/no fixed deadline",
    "eligibility": "..."
  }}
]

Do NOT include a "url" field - that will be looked up separately.
If none of the search results qualify, respond with an empty array: []
"""

    candidates = generate_json(prompt)

    validated = []
    for item in candidates:
        deadline = item.get("deadline")

        if not _deadline_is_valid(deadline, target_month):
            continue

        title = item.get("title", "")
        organization = item.get("organization", "")
        official_url = _find_official_url(title, organization)

        if not official_url or not is_link_valid(official_url):
            continue
        if _mentions_stale_year(official_url):
            continue

        item["url"] = official_url
        validated.append(item)

    return validated
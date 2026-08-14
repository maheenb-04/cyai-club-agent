import re

from app.services.tavily_client import search_web
from app.services.mistral_client import generate_json
from app.services.link_validator import is_link_valid

AGGREGATOR_DOMAINS = [
    "scholarships360.org",
    "bigfuture.collegeboard.org",
    "cappex.com",
    "fastweb.com",
    "unigo.com",
    "niche.com",
    "chegg.com",
]

REFERENCE_DOMAINS = [
    "wikipedia.org",
    "reddit.com",
    "quora.com",
    "youtube.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
]

STALE_YEAR_PATTERN = re.compile(r"20(1[0-9]|2[0-5])\b")


def _is_rejected(url: str) -> bool:
    return any(d in url for d in AGGREGATOR_DOMAINS) or any(d in url for d in REFERENCE_DOMAINS)


def _mentions_stale_year(text: str) -> bool:
    return bool(STALE_YEAR_PATTERN.search(text))


def _find_official_url(title: str, organization: str) -> str:
    query = f"{title} {organization} 2026 official apply application program"
    results = search_web(query, max_results=6)

    candidates = [r for r in results if not _is_rejected(r["url"])]
    if not candidates:
        return ""

    candidate_text = "\n".join(
        f"{i}. URL: {c['url']}\n   Title: {c['title']}\n   Snippet: {c['content'][:200]}"
        for i, c in enumerate(candidates)
    )

    prompt = f"""I'm looking for the OFFICIAL, CURRENT (2026) application page for this program:
Title: {title}
Organization: {organization}

Candidates:
{candidate_text}

Pick the ONE candidate most likely to be the official, current 2026 application page - the program's own site or a direct application portal, NOT a reference/social media page.
Avoid results clearly referencing an old cycle (2022-2025) unless it's the only option.
Respond with ONLY a JSON array: [{{"index": <number>}}] or [{{"index": -1}}] if none fit.
"""

    choice = generate_json(prompt)
    if not choice or not isinstance(choice, list):
        return candidates[0]["url"]

    index = choice[0].get("index", -1)
    if index == -1 or index >= len(candidates):
        return candidates[0]["url"]

    return candidates[index]["url"]


def _search_and_extract(search_query: str, extraction_prompt: str, category: str, max_results: int = 8) -> list[dict]:
    search_results = search_web(search_query, max_results=max_results)
    if not search_results:
        return []

    context = "\n\n".join(
        f"Source: {r['url']}\nTitle: {r['title']}\nContent: {r['content'][:1000]}"
        for r in search_results
    )

    prompt = extraction_prompt.format(context=context)
    candidates = generate_json(prompt)

    validated = []
    for item in candidates:
        title = item.get("title", "")
        organization = item.get("organization", "")
        official_url = _find_official_url(title, organization)

        if not official_url or not is_link_valid(official_url):
            continue
        if _mentions_stale_year(official_url) or _is_rejected(official_url):
            continue

        item["url"] = official_url
        item["category"] = category
        validated.append(item)

    return validated


def find_tech_prep_programs(max_results: int = 8) -> list[dict]:
    query = "tech prep program undergraduate cybersecurity AI 2026 NYC CUNY open application"
    prompt = """You are helping a college cybersecurity/AI club find CURRENT, OPEN tech-prep / training programs for undergraduate students.

Below are real web search results. Extract ONLY specific named tech-prep, coding bootcamp, or structured training programs that:
1. Are genuinely open for applications now or upcoming in 2026 (not expired)
2. Are open to undergraduate students nationally, remotely, or in NYC
3. Are relevant to cybersecurity, AI, or technology fields
4. Are a SPECIFIC named program (not a general listing article)

Search results:
{context}

Respond with ONLY a JSON array, no other text:
[
  {{
    "title": "...",
    "organization": "...",
    "description": "...",
    "deadline": "... or null if rolling",
    "eligibility": "..."
  }}
]
If none qualify, respond with: []
"""
    return _search_and_extract(query, prompt, "bootcamp", max_results)


def find_residency_programs(max_results: int = 8) -> list[dict]:
    query = "tech residency program undergraduate cybersecurity AI 2026 open application no experience"
    prompt = """You are helping a college cybersecurity/AI club find CURRENT, OPEN residency programs for undergraduate/early-career students.

Below are real web search results. Extract ONLY specific named residency programs (structured entry-level programs with mentorship/stipend, NOT requiring years of professional experience) that:
1. Are genuinely open for applications now or upcoming in 2026 (not expired)
2. Are open to undergraduate students or recent grads nationally, remotely, or in NYC
3. Are relevant to cybersecurity, AI, or technology fields
4. Do NOT require multiple years of professional experience
5. Are a SPECIFIC named program (not a general listing article)

Search results:
{context}

Respond with ONLY a JSON array, no other text:
[
  {{
    "title": "...",
    "organization": "...",
    "description": "...",
    "deadline": "... or null if rolling",
    "eligibility": "..."
  }}
]
If none qualify, respond with: []
"""
    return _search_and_extract(query, prompt, "fellowship", max_results)

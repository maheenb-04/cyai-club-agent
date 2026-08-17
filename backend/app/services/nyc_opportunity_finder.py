import re

from app.services.tavily_client import search_web
from app.services.mistral_client import generate_json
from app.services.link_validator import is_link_valid

REFERENCE_DOMAINS = [
    "wikipedia.org", "reddit.com", "quora.com", "youtube.com",
    "facebook.com", "twitter.com", "x.com", "instagram.com",
]

LISTING_PAGE_DOMAINS = [
    "linkedin.com/jobs/",
    "joinhandshake.com/internships/",
    "wayup.com/s/internships",
    "indeed.com/jobs",
]

STALE_YEAR_PATTERN = re.compile(r"20(1[0-9]|2[0-4])\b")

NYC_SEARCH_QUERIES = [
    "NYC internship cybersecurity fall 2026 undergraduate apply",
    "New York tri-state tech internship 2026 entry level",
    "NYC data analyst internship 2026 undergraduate",
    "New York information technology emerging talent internship 2026",
    "NYC IT internship fall 2026 no experience required",
    "tri-state area cybersecurity internship 2026 college students",
]


def _is_rejected(url: str) -> bool:
    return any(d in url for d in REFERENCE_DOMAINS)


def _is_generic_listing_page(url: str) -> bool:
    return any(d in url for d in LISTING_PAGE_DOMAINS)


def _mentions_stale_year(text: str) -> bool:
    return bool(STALE_YEAR_PATTERN.search(text))


def _find_direct_url(title: str, organization: str) -> str:
    query = f"{title} {organization} apply direct job posting careers page"
    results = search_web(query, max_results=5)

    candidates = [
        r for r in results
        if not _is_rejected(r["url"]) and not _is_generic_listing_page(r["url"])
    ]
    if not candidates:
        return ""

    candidate_text = "\n".join(
        f"{i}. URL: {c['url']}\n   Title: {c['title']}\n   Snippet: {c['content'][:200]}"
        for i, c in enumerate(candidates)
    )

    prompt = f"""I'm looking for the DIRECT, SPECIFIC application page for this exact position:
Title: {title}
Organization: {organization}

Candidates:
{candidate_text}

Pick the ONE candidate that goes directly to THIS SPECIFIC job posting (the company's own careers site or ATS like Greenhouse/Workday/SmartRecruiters) - NOT a generic search results or listing page.
Respond with ONLY a JSON array: [{{"index": <number>}}] or [{{"index": -1}}] if none are a good direct match.
"""

    choice = generate_json(prompt)
    if not choice or not isinstance(choice, list):
        return ""

    index = choice[0].get("index", -1)
    if index == -1 or index >= len(candidates):
        return ""

    return candidates[index]["url"]


def find_nyc_opportunities(max_results_per_query: int = 5) -> list[dict]:
    all_candidates = []

    for query in NYC_SEARCH_QUERIES:
        results = search_web(query, max_results=max_results_per_query)
        for r in results:
            if _is_rejected(r["url"]) or _mentions_stale_year(r["url"]):
                continue
            all_candidates.append(r)

    if not all_candidates:
        return []

    context = "\n\n".join(
        f"Source: {r['url']}\nTitle: {r['title']}\nContent: {r['content'][:800]}"
        for r in all_candidates
    )

    prompt = f"""You are helping a college cybersecurity/AI club in New York City find CURRENT, OPEN internships and entry-level opportunities specifically for undergraduate students.

Below are real web search results. Extract ONLY opportunities that:
1. Are genuinely open for applications now or upcoming for Fall 2026 / Summer 2027 (not expired, not old cycles)
2. Are located in New York City, Long Island, or the broader tri-state area (NY/NJ/CT), OR are explicitly fully remote
3. DO NOT include anything located outside the NYC tri-state area (e.g., Texas, California, other states) unless remote
4. Are relevant to technology, cybersecurity, AI, data, or IT fields
5. Are genuinely entry-level / internship-level - do NOT require years of professional experience
6. Are a SPECIFIC named opportunity at a SPECIFIC real company or organization (not a general listing article or aggregator page)

Search results:
{context}

Respond with ONLY a JSON array, no other text, in this exact format:
[
  {{
    "title": "...",
    "organization": "...",
    "description": "...",
    "deadline": "... or null if rolling/not specified",
    "eligibility": "... including location/remote status",
    "category": "internship or fellowship or job"
  }}
]

Do NOT include a "url" field - that will be looked up separately for each item.
If none of the search results qualify, respond with an empty array: []
"""

    candidates = generate_json(prompt)

    validated = []
    for item in candidates:
        title = item.get("title", "")
        organization = item.get("organization", "")

        direct_url = _find_direct_url(title, organization)
        if not direct_url or not is_link_valid(direct_url):
            continue
        if _is_rejected(direct_url) or _mentions_stale_year(direct_url) or _is_generic_listing_page(direct_url):
            continue

        item["url"] = direct_url
        validated.append(item)

    return validated

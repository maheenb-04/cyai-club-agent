import re
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"

JOB_KEYWORDS = [
    "entry level cybersecurity analyst",
    "entry level information security analyst",
    "associate cybersecurity analyst",
    "entry level artificial intelligence analyst",
]

INTERNSHIP_KEYWORDS = [
    "cybersecurity internship",
    "AI internship",
    "information security internship",
    "machine learning internship",
    "data security internship",
    "SOC analyst internship",
    "network security internship",
    "AI research internship",
    "cyber defense internship",
    "IT security internship",
    "fall 2026 internship cybersecurity",
    "fall 2026 internship AI",
    "summer 2027 internship cybersecurity",
]

EXCLUDE_TITLE_KEYWORDS = [
    "vp", "vice president", "director", "chief", "principal", "head of",
    "svp", "evp", "cto", "ciso", "cio", "senior manager", "executive",
    "architect", "staff engineer", "lead ", " iv", " iii", "scientist",
    "sr.", "sr ", "senior", "manager", "phd", "postdoc", "masters", "mba",
    "junior", "jr.", "jr ", "ii",
]

MAX_EXPERIENCE_YEARS = 2
MAX_POSTING_AGE_DAYS = 30

YEARS_RANGE_PATTERN = re.compile(r"(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*\+?\s*years?", re.IGNORECASE)
YEARS_MINIMUM_PATTERN = re.compile(r"(\d{1,2})\s*\+\s*years?", re.IGNORECASE)


def _is_appropriate_title(title: str) -> bool:
    lowered = title.lower()
    return not any(keyword in lowered for keyword in EXCLUDE_TITLE_KEYWORDS)


def _requires_too_much_experience(description: str, max_years: int = MAX_EXPERIENCE_YEARS) -> bool:
    if not description:
        return False

    for low, high in YEARS_RANGE_PATTERN.findall(description):
        if int(low) > max_years:
            return True

    text_without_ranges = YEARS_RANGE_PATTERN.sub("", description)

    for num in YEARS_MINIMUM_PATTERN.findall(text_without_ranges):
        if int(num) > max_years:
            return True

    return False


def _is_recent(created_str: str) -> bool:
    if not created_str:
        return True
    try:
        created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
    except ValueError:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_POSTING_AGE_DAYS)
    return created >= cutoff


def _fetch_keyword_batch(keyword: str, results_per_keyword: int, category_label: str) -> list[dict]:
    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_api_key,
        "what": keyword,
        "results_per_page": results_per_keyword,
        "content-type": "application/json",
    }

    response = httpx.get(ADZUNA_BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    opportunities = []
    for job in data.get("results", []):
        title = job.get("title", "Untitled Position")
        description = job.get("description", "") or ""

        if not _is_appropriate_title(title):
            continue
        if not _is_recent(job.get("created", "")):
            continue
        if _requires_too_much_experience(description):
            continue
        if category_label == "internship" and "intern" not in title.lower():
            continue

        location = job.get("location", {}).get("display_name")

        opportunities.append({
            "category": category_label,
            "title": title,
            "organization": job.get("company", {}).get("display_name"),
            "description": description[:500],
            "url": job.get("redirect_url", ""),
            "deadline": None,
            "eligibility": f"Location: {location}" if location else None,
            "source": f"adzuna:{job.get('id')}",
            "source_type": "live_api",
        })

    return opportunities


def fetch_adzuna_jobs(results_per_keyword: int = 8) -> list[dict]:
    opportunities = []
    for keyword in JOB_KEYWORDS:
        opportunities.extend(_fetch_keyword_batch(keyword, results_per_keyword, "job"))
    return opportunities


def fetch_adzuna_internships(results_per_keyword: int = 12) -> list[dict]:
    opportunities = []
    for keyword in INTERNSHIP_KEYWORDS:
        opportunities.extend(_fetch_keyword_batch(keyword, results_per_keyword, "internship"))
    return opportunities

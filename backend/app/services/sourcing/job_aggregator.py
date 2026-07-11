import httpx

from app.config import settings

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"

SEARCH_KEYWORDS = ["cybersecurity", "artificial intelligence", "information security"]


def fetch_adzuna_jobs(results_per_keyword: int = 10) -> list[dict]:
    opportunities = []

    for keyword in SEARCH_KEYWORDS:
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

        for job in data.get("results", []):
            opportunities.append({
                "category": "job",
                "title": job.get("title", "Untitled Position"),
                "organization": job.get("company", {}).get("display_name"),
                "description": (job.get("description", "") or "")[:500],
                "url": job.get("redirect_url", ""),
                "deadline": None,
                "eligibility": None,
                "source": f"adzuna:{job.get('id')}",
                "source_type": "live_api",
            })

    return opportunities
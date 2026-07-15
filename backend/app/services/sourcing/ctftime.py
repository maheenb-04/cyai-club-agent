from datetime import datetime, timezone

import httpx

CTFTIME_API_URL = "https://ctftime.org/api/v1/events/"


def fetch_upcoming_ctf_events(limit: int = 20) -> list[dict]:
    now = datetime.now(timezone.utc)
    params = {
        "limit": limit,
        "start": int(now.timestamp()),
    }

    headers = {"User-Agent": "CYAI-Club-Agent/1.0"}

    response = httpx.get(CTFTIME_API_URL, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    events = response.json()

    opportunities = []
    for event in events:
        title = event.get("title", "Untitled CTF")

        if "cancelled" in title.lower() or "canceled" in title.lower():
            continue

        start_str = event.get("start", "")
        deadline_display = start_str.split("T")[0] if start_str else None

        opportunities.append({
            "category": "ctf",
            "title": title,
            "organization": event.get("organizers", [{}])[0].get("name") if event.get("organizers") else None,
            "description": event.get("description", "")[:500],
            "url": event.get("url") or event.get("ctftime_url", ""),
            "deadline": deadline_display,
            "eligibility": None,
            "source": f"ctftime:{event.get('id')}",
            "source_type": "live_api",
        })

    return opportunities

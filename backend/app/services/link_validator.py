import time

import httpx


def is_safe_url(url: str) -> bool:
    if not url:
        return False
    return url.strip().lower().startswith(("http://", "https://"))


def _single_check(url: str, timeout: float) -> bool:
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CYAI-Club-Agent link checker"},
        )
        return response.status_code < 400
    except httpx.RequestError:
        return False
    except Exception:
        return False


def is_link_valid(url: str, timeout: float = 12.0, retries: int = 2) -> bool:
    if not is_safe_url(url):
        return False

    for attempt in range(retries):
        if _single_check(url, timeout):
            return True
        if attempt < retries - 1:
            time.sleep(1.5)

    return False

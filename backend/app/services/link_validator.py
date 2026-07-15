import httpx


def is_safe_url(url: str) -> bool:
    if not url:
        return False
    return url.strip().lower().startswith(("http://", "https://"))


def is_link_valid(url: str, timeout: float = 8.0) -> bool:
    if not is_safe_url(url):
        return False

    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (CYAI-Club-Agent link checker)"},
        )
        return response.status_code < 400
    except httpx.RequestError:
        return False
    except Exception:
        return False

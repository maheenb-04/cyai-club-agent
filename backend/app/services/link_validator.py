import httpx


def is_link_valid(url: str, timeout: float = 8.0) -> bool:
    if not url or not url.startswith("http"):
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
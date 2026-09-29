import json
import time

from mistralai.client import Mistral
from mistralai.client.errors.sdkerror import SDKError

from app.config import settings

_client = Mistral(api_key=settings.mistral_api_key)


class MistralUnavailableError(Exception):
    """Raised when Mistral can't fulfill a request after retries (rate limit, outage, etc.)."""


def _is_rate_limited(exc: SDKError) -> bool:
    text = str(exc).lower()
    return "429" in text or "rate_limited" in text or "rate limit" in text


def generate_json(prompt: str, model: str = "mistral-small-latest", max_retries: int = 3) -> list[dict]:
    last_exc = None
    for attempt in range(max_retries):
        try:
            response = _client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout_ms=30000,
            )
            break
        except SDKError as exc:
            last_exc = exc
            if _is_rate_limited(exc) and attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            if _is_rate_limited(exc):
                raise MistralUnavailableError(
                    "Mistral API rate limit exceeded after retries. Try again in a few minutes."
                ) from exc
            raise MistralUnavailableError(f"Mistral API error: {exc}") from exc
    else:
        raise MistralUnavailableError(
            "Mistral API rate limit exceeded after retries. Try again in a few minutes."
        ) from last_exc

    text = response.choices[0].message.content.strip()

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []

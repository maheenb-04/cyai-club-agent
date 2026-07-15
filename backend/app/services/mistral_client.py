import json

from mistralai.client import Mistral

from app.config import settings

_client = Mistral(api_key=settings.mistral_api_key)


def generate_json(prompt: str, model: str = "mistral-small-latest") -> list[dict]:
    response = _client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        timeout_ms=30000,
    )

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

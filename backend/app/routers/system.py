import smtplib

from fastapi import APIRouter, Depends

from app.config import settings
from app.core.security import verify_api_key

router = APIRouter(prefix="/system", tags=["system"])


def _check_configured(value: str, placeholder_hints: list) -> bool:
    if not value:
        return False
    lowered = value.lower()
    return not any(hint in lowered for hint in placeholder_hints)


@router.get("/status", dependencies=[Depends(verify_api_key)])
def system_status(deep_check: bool = False):
    status = {
        "mistral_api_key": "configured" if _check_configured(settings.mistral_api_key, ["your_mistral", "placeholder"]) else "missing",
        "tavily_api_key": "configured" if _check_configured(settings.tavily_api_key, ["your_tavily", "placeholder"]) else "missing",
        "adzuna_app_id": "configured" if _check_configured(settings.adzuna_app_id, ["your_adzuna", "placeholder"]) else "missing",
        "adzuna_api_key": "configured" if _check_configured(settings.adzuna_api_key, ["your_adzuna", "placeholder"]) else "missing",
        "gmail_address": "configured" if _check_configured(settings.gmail_address, ["your_club_email", "placeholder"]) else "missing",
        "gmail_app_password": "configured" if _check_configured(settings.gmail_app_password, ["your_16_char", "placeholder"]) else "missing",
        "token_secret_key": "configured" if _check_configured(settings.token_secret_key, ["generate_a_random", "placeholder"]) else "missing",
        "agent_api_key": "configured" if _check_configured(settings.agent_api_key, ["your_agent", "placeholder"]) else "missing",
    }

    if deep_check:
        smtp_result = "not_tested"
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
                server.starttls()
                server.login(settings.gmail_address, settings.gmail_app_password)
            smtp_result = "connected_successfully"
        except Exception as e:
            smtp_result = f"failed: {str(e)[:150]}"

        status["gmail_smtp_live_test"] = smtp_result

    all_configured = all(v == "configured" for v in status.values() if v in ("configured", "missing"))
    status["overall"] = "all_systems_configured" if all_configured else "some_keys_missing_or_placeholder"

    return status

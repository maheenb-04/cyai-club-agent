import re
from datetime import date

from dateutil import parser as date_parser


def _parse_deadline(deadline_str: str):
    if not deadline_str:
        return None
    lowered = deadline_str.strip().lower()
    if lowered in ("none", "null", "rolling", "n/a", "rolling/no fixed deadline"):
        return None
    try:
        parsed = date_parser.parse(deadline_str, fuzzy=True)
        return parsed.date()
    except (ValueError, OverflowError):
        return None


def expire_old_opportunities(db) -> int:
    from app import models

    today = date.today()
    active_opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.is_active == True
    ).all()

    expired_count = 0
    for opp in active_opportunities:
        parsed = _parse_deadline(opp.deadline)
        if parsed and parsed < today:
            opp.is_active = False
            expired_count += 1

    db.commit()
    return expired_count


SEASON_START_MONTH = {
    "spring": 1,
    "summer": 6,
    "fall": 9,
    "autumn": 9,
    "winter": 12,
}

SEASON_YEAR_PATTERN = re.compile(
    r"\b(spring|summer|fall|autumn|winter)\s+(20\d{2})\b", re.IGNORECASE
)


def _find_stale_season(text: str, today: date) -> bool:
    if not text:
        return False

    matches = SEASON_YEAR_PATTERN.findall(text)
    if not matches:
        return False

    for season, year_str in matches:
        season = season.lower()
        year = int(year_str)
        start_month = SEASON_START_MONTH.get(season)
        if not start_month:
            continue

        cutoff = date(year, start_month, 1)
        if today >= cutoff:
            return True

    return False


def expire_stale_seasonal_opportunities(db) -> int:
    from app import models

    today = date.today()
    active_opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.is_active == True
    ).all()

    expired_count = 0
    for opp in active_opportunities:
        combined_text = f"{opp.title or ''} {opp.description or ''}"
        if _find_stale_season(combined_text, today):
            opp.is_active = False
            expired_count += 1

    db.commit()
    return expired_count

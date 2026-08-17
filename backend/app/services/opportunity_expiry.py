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

SEASON_WORD_PATTERN = re.compile(r"\b(spring|summer|fall|autumn|winter)\b", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")


def _find_stale_season(title: str, today: date) -> bool:
    if not title:
        return False

    season_matches = list(set(m.lower() for m in SEASON_WORD_PATTERN.findall(title)))
    year_matches = list(set(YEAR_PATTERN.findall(title)))

    if len(season_matches) != 1 or len(year_matches) != 1:
        return False

    season = season_matches[0]
    year = int(year_matches[0])
    start_month = SEASON_START_MONTH.get(season)
    if not start_month:
        return False

    cutoff = date(year, start_month, 1)
    return today >= cutoff


def expire_stale_seasonal_opportunities(db) -> int:
    from app import models

    today = date.today()
    active_opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.is_active == True
    ).all()

    expired_count = 0
    for opp in active_opportunities:
        if _find_stale_season(opp.title, today):
            opp.is_active = False
            expired_count += 1

    db.commit()
    return expired_count

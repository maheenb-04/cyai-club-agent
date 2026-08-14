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

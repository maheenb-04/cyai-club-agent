from app.services.link_validator import is_link_valid


def check_and_deactivate_dead_links(db):
    from datetime import datetime
    from app import models

    active_opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.is_active == True
    ).all()

    deactivated_count = 0
    valid_count = 0

    for opp in active_opportunities:
        is_valid = is_link_valid(opp.url)
        opp.last_validated_at = datetime.utcnow()

        if is_valid:
            opp.link_status = "valid"
            valid_count += 1
        else:
            opp.link_status = "dead"
            opp.is_active = False
            deactivated_count += 1

    db.commit()
    return {"checked": len(active_opportunities), "valid": valid_count, "deactivated": deactivated_count}

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app import models
from app.services.sourcing.ctftime import fetch_upcoming_ctf_events
from app.services.sourcing.job_aggregator import fetch_adzuna_jobs, fetch_adzuna_internships
from app.services.scholarship_finder import find_scholarships
from app.services.program_finder import find_tech_prep_programs, find_residency_programs

logger = logging.getLogger("cyai_scheduler")

scheduler = BackgroundScheduler()


def _save_items(items: list, db):
    added = 0
    for item in items:
        exists = db.query(models.Opportunity).filter(
            models.Opportunity.source == item.get("source", item.get("url", ""))
        ).first()
        if exists:
            continue
        source = item.get("source") or f"auto_search:{item.get('url', '')}"
        db.add(models.Opportunity(
            category=item.get("category", "job"),
            title=item.get("title", "Untitled"),
            organization=item.get("organization"),
            description=item.get("description"),
            url=item.get("url", ""),
            deadline=item.get("deadline"),
            eligibility=item.get("eligibility"),
            source=source,
            source_type=item.get("source_type", "auto_scheduled"),
        ))
        added += 1
    db.commit()
    return added


def scheduled_daily_sync():
    logger.info("Running scheduled daily sync (CTFtime + Adzuna)")
    db = SessionLocal()
    try:
        ctf_items = fetch_upcoming_ctf_events(limit=20)
        added_ctf = _save_items(ctf_items, db)

        job_items = fetch_adzuna_jobs(results_per_keyword=8)
        added_jobs = _save_items(job_items, db)

        intern_items = fetch_adzuna_internships(results_per_keyword=12)
        added_interns = _save_items(intern_items, db)

        logger.info(f"Daily sync complete: {added_ctf} CTFs, {added_jobs} jobs, {added_interns} internships added")
    except Exception as e:
        logger.error(f"Daily sync failed: {e}")
    finally:
        db.close()


def scheduled_weekly_search():
    logger.info("Running scheduled weekly AI search (scholarships, tech-prep, residencies)")
    db = SessionLocal()
    try:
        scholarships = find_scholarships("current")
        for s in scholarships:
            s["source"] = f"ai_search:{s.get('url', '')}"
            s["category"] = "scholarship"
            s["source_type"] = "ai_search"
        added_sch = _save_items(scholarships, db)

        tech_prep = find_tech_prep_programs()
        for t in tech_prep:
            t["source"] = f"ai_search:{t.get('url', '')}"
            t["source_type"] = "ai_search"
        added_tech = _save_items(tech_prep, db)

        residencies = find_residency_programs()
        for r in residencies:
            r["source"] = f"ai_search:{r.get('url', '')}"
            r["source_type"] = "ai_search"
        added_res = _save_items(residencies, db)

        logger.info(f"Weekly search complete: {added_sch} scholarships, {added_tech} tech-prep, {added_res} residencies added")
    except Exception as e:
        logger.error(f"Weekly search failed: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(scheduled_daily_sync, "interval", hours=24, id="daily_sync", replace_existing=True)
    scheduler.add_job(scheduled_weekly_search, "interval", days=7, id="weekly_search", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started: daily sync (24h), weekly AI search (7d)")

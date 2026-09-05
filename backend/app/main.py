import sys
import asyncio
import os

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.database import engine, Base, SessionLocal
from app import models
from app.routers import opportunities, curated_sources, members, newsletters, events, social_posts, system
from app.core.security import verify_api_key
from app.core.limiter import limiter
from app.core.scheduler import start_scheduler, scheduled_daily_sync, scheduled_weekly_search
from app.services.opportunity_expiry import expire_old_opportunities
from app.services.link_cleanup import check_and_deactivate_dead_links

Base.metadata.create_all(bind=engine)

os.makedirs("app/uploads/events", exist_ok=True)
os.makedirs("app/uploads/newsletter_attachments", exist_ok=True)

app = FastAPI(title="CYAI Club Assistant Agent")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://cyai-club-assistant.onrender.com",
        "https://cyai-club-agent-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")
app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")

app.include_router(opportunities.router, dependencies=[Depends(verify_api_key)])
app.include_router(curated_sources.router, dependencies=[Depends(verify_api_key)])
app.include_router(members.router)
app.include_router(newsletters.router, dependencies=[Depends(verify_api_key)])
app.include_router(events.router, dependencies=[Depends(verify_api_key)])
app.include_router(social_posts.router, dependencies=[Depends(verify_api_key)])
app.include_router(system.router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/")
def health_check():
    return {"status": "ok", "service": "cyai-club-agent"}


@app.post("/system/seed-additional-items", dependencies=[Depends(verify_api_key)])
def seed_additional_items():
    db = SessionLocal()
    try:
        items = [
            {
                "category": "bootcamp",
                "title": "Cyber Security Operations Job Simulation",
                "organization": "Datacom (via Forage)",
                "description": "Investigate a cyberattack and conduct a comprehensive risk assessment as if working on Datacom's Cyber Security Operations team. Free, self-paced, 3-4 hours.",
                "url": "https://www.theforage.com/simulations/datacom/cybersecurity-zm6d",
                "deadline": None,
                "eligibility": "Open to all students, no prior experience required.",
            },
            {
                "category": "bootcamp",
                "title": "Automation AI Accelerator Job Simulation",
                "organization": "Datacom (via Forage)",
                "description": "Advise a client on automating their timesheet-to-invoice process as an Automation Developer, progressing from AI Pilot to AI Architect to Business Strategist. Free, self-paced, 4-5 hours.",
                "url": "https://www.theforage.com/simulations/datacom/automation-zn3l",
                "deadline": None,
                "eligibility": "Intermediate level, open to all students.",
            },
            {
                "category": "bootcamp",
                "title": "Partnering with AI in the Workplace Job Simulation",
                "organization": "Datacom (via Forage)",
                "description": "Use AI to plan, design, and problem-solve alongside a cross-functional team in a future-focused workplace simulation, practicing AI collaboration, prompt writing, and real code. Free, self-paced, 3-4 hours.",
                "url": "https://www.theforage.com/simulations/datacom/partnering-with-ai-in-the-workplace-khv2",
                "deadline": None,
                "eligibility": "Intermediate level, open to all students.",
            },
            {
                "category": "bootcamp",
                "title": "Introduction to Cloud Job Simulation",
                "organization": "Datacom (via Forage)",
                "description": "Help a client migrate to cloud-based services, learning to register an application on the cloud and create a GitHub Action workflow. Free, self-paced, 2-3 hours, no prior tech experience needed.",
                "url": "https://www.theforage.com/simulations/datacom/intro-cloud-yfvk",
                "deadline": None,
                "eligibility": "Introductory level, open to all students including those with minimal tech background.",
            },
        ]

        added = 0
        for item in items:
            exists = db.query(models.Opportunity).filter(models.Opportunity.url == item["url"]).first()
            if exists:
                continue
            db.add(models.Opportunity(
                category=item["category"],
                title=item["title"],
                organization=item["organization"],
                description=item["description"],
                url=item["url"],
                deadline=item["deadline"],
                eligibility=item["eligibility"],
                source=f"manual_add:{item['url']}",
                source_type="manual",
            ))
            added += 1

        db.commit()
        return {"added_opportunities": added}
    finally:
        db.close()


@app.post("/system/trigger-daily-sync", dependencies=[Depends(verify_api_key)])
def trigger_daily_sync():
    scheduled_daily_sync()
    return {"detail": "Daily sync triggered manually"}


@app.post("/system/trigger-weekly-search", dependencies=[Depends(verify_api_key)])
def trigger_weekly_search():
    scheduled_weekly_search()
    return {"detail": "Weekly AI search triggered manually"}


@app.post("/system/expire-old-opportunities", dependencies=[Depends(verify_api_key)])
def trigger_expiry_check():
    db = SessionLocal()
    try:
        expired_count = expire_old_opportunities(db)
        return {"expired_count": expired_count}
    finally:
        db.close()


@app.post("/system/check-and-clean-dead-links", dependencies=[Depends(verify_api_key)])
def trigger_link_cleanup():
    db = SessionLocal()
    try:
        result = check_and_deactivate_dead_links(db)
        return result
    finally:
        db.close()

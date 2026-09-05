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
                "category": "job",
                "title": "Data for Good Hackathon - Data & AI Program - 2027 Summer Internship",
                "organization": "JPMorgan Chase",
                "description": "A two-day hackathon solving real nonprofit data problems alongside JPMorganChase's Tech for Social Good team, held in Brooklyn, NY. Participation may lead to consideration for the 2027 Data & AI Program summer internship, building end-to-end data, analytics, and ML solutions.",
                "url": "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210775223",
                "deadline": None,
                "eligibility": "Pursuing a Bachelor's or Master's degree in a quantitative or technical discipline (Data Science, ML, CS, or Math), graduating December 2027-August 2028. Must be authorized to work in the U.S. No prior experience required.",
            },
            {
                "category": "job",
                "title": "NY Chamber of Commerce Business Expo",
                "organization": "CUNY Borough of Manhattan Community College",
                "description": "The 25th Annual Chamber Business Expo, Metropolitan NY's longest-running regional business fair, held in-person at BMCC. Companies attending include AWS, IBM, Google, LinkedIn, and Microsoft, with hands-on workshops (Google's Grow with Google, AWS no-code/low-code workshop, IBM career panel) and a main-stage AI panel on business, education, and technology.",
                "url": "https://york-cuny.joinhandshake.com/stu/career_fairs/68952",
                "deadline": "2026-09-17",
                "eligibility": "Free attendance. Business casual attire recommended; bring resume copies.",
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

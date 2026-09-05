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


@app.post("/system/seed-nypd-items", dependencies=[Depends(verify_api_key)])
def seed_nypd_items():
    db = SessionLocal()
    try:
        items = [
            {
                "title": "ITB Customer Service Intern",
                "organization": "NYPD Information Technology Bureau",
                "description": "Provide citywide technical diagnostics, active-directory administration, queue management, and hardware provisioning. Manage ServiceNow incidents, support citywide endpoint systems, and coordinate Dell warranty repairs.",
                "url": "https://york-cuny.joinhandshake.com/jobs/11383742",
                "deadline": "2026-10-03",
                "eligibility": "Part-time, 20 hrs/week, onsite NYC, October 1 2026-May 31 2027. Knowledge of Active Directory, DNS, DHCP, TCP/IP preferred.",
            },
            {
                "title": "Information Security Intern",
                "organization": "NYPD Information Technology Bureau",
                "description": "Support Vulnerability Management & Remediation (VMR) projects - document requirements, track tactical plans, build workflow diagrams, and research VMR capabilities in existing security solutions.",
                "url": "https://york-cuny.joinhandshake.com/jobs/11384293",
                "deadline": "2026-10-03",
                "eligibility": "Part-time, 20 hrs/week, onsite NYC, October 1 2026-May 31 2027.",
            },
            {
                "title": "Active Directory / Cloud Intern",
                "organization": "NYPD Information Technology Bureau",
                "description": "Design and support enterprise identity, directory, and Microsoft cloud-platform services - Active Directory, Microsoft Entra ID, hybrid identity, Microsoft 365, Power Platform, and Azure DevOps.",
                "url": "https://york-cuny.joinhandshake.com/jobs/11383988",
                "deadline": "2026-10-03",
                "eligibility": "Part-time, 20 hrs/week, onsite NYC, October 1 2026-May 31 2027. AD, Entra ID, PowerShell knowledge preferred.",
            },
            {
                "title": "Data Center Operations Intern",
                "organization": "NYPD Information Technology Bureau",
                "description": "Coordinate operations, infrastructure projects, and lifecycle activities across multiple large-scale NYPD data centers, including hardware installs, cabling, power distribution, and vendor management.",
                "url": "https://york-cuny.joinhandshake.com/jobs/11385442",
                "deadline": "2026-10-03",
                "eligibility": "Part-time, 20 hrs/week, onsite NYC, October 1 2026-May 31 2027.",
            },
            {
                "title": "Application Division Intern",
                "organization": "NYPD Information Technology Bureau",
                "description": "Build wireframes and prototypes in Figma, map operational workflows, support backlog prioritization, and run usability testing for department tools.",
                "url": "https://york-cuny.joinhandshake.com/jobs/11385516",
                "deadline": "2026-10-03",
                "eligibility": "Part-time, 20 hrs/week, onsite NYC, October 1 2026-May 31 2027. UX/UI, HCI, or related field.",
            },
            {
                "title": "IT Fiscal Affairs Intern",
                "organization": "NYPD Information Technology Bureau",
                "description": "Support IT fiscal operations - procurement and contract tracking, invoice intake, and financial data compilation across the full IT budget workflow.",
                "url": "https://york-cuny.joinhandshake.com/jobs/11385485",
                "deadline": "2026-10-03",
                "eligibility": "Part-time, 20 hrs/week, onsite NYC, October 1 2026-May 31 2027. Business, Finance, Accounting, Data Analytics, or related field.",
            },
            {
                "title": "Unified Communication Intern",
                "organization": "NYPD Information Technology Bureau",
                "description": "Support enterprise unified communications, VoIP, and audiovisual/conference-room technologies, including Cisco Unified Communications Manager and conference-room AV systems.",
                "url": "https://york-cuny.joinhandshake.com/jobs/11385411",
                "deadline": "2026-10-03",
                "eligibility": "Part-time, 20 hrs/week, onsite NYC, October 1 2026-May 31 2027.",
            },
            {
                "title": "Data Transmission Intern",
                "organization": "NYPD Information Technology Bureau",
                "description": "Support secure data transmission infrastructure - network and application delivery security, digital certificate administration, TLS configuration, and secure file-transfer platforms.",
                "url": "https://york-cuny.joinhandshake.com/jobs/11385239",
                "deadline": "2026-10-03",
                "eligibility": "Part-time, 20 hrs/week, onsite NYC, October 1 2026-May 31 2027.",
            },
        ]

        added = 0
        for item in items:
            exists = db.query(models.Opportunity).filter(models.Opportunity.url == item["url"]).first()
            if exists:
                continue
            db.add(models.Opportunity(
                category="internship",
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

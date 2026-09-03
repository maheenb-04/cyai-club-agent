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


@app.post("/system/seed-september-items", dependencies=[Depends(verify_api_key)])
def seed_september_items():
    db = SessionLocal()
    try:
        new_opportunities = [
            {
                "category": "internship",
                "title": "CUNY Spring Forward Internship Program",
                "organization": "CUNY",
                "description": "A paid internship program for CUNY undergrads with no prior paid internship experience, including a STEM/Green Industry Hub track.",
                "url": "https://www.cuny.edu/about/administration/offices/ocip/students/spring-forward/",
                "deadline": None,
                "eligibility": "CUNY undergraduate this Fall 2026 and Spring 2027, 18+ by September 8th 2026, GPA 2.0 or above.",
            },
            {
                "category": "internship",
                "title": "Break Through Tech Sprinternships",
                "organization": "Break Through Tech",
                "description": "A paid, three-week micro-internship in January 2027, matching students with a local NYC employer during winter break. Includes hands-on projects, professional development, and networking.",
                "url": "https://breakthroughtech.tfaforms.net/w/SPR-AY-2026-27-Application",
                "deadline": "2026-09-27",
                "eligibility": "Open to CUNY students; apply early, decisions by October 9th 2026.",
            },
            {
                "category": "job",
                "title": "2027 Code for Good Hackathon - Software Engineer Program",
                "organization": "JPMorgan Chase",
                "description": "A two-day hackathon (Oct 16-17) building a tech solution for a nonprofit. Participation may lead to consideration for the 2027 Software Engineer Summer Internship.",
                "url": "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210773759",
                "deadline": None,
                "eligibility": "Graduating December 2027-June 2028, CS/IS/IT/Data Science/AI/Big Data or related fields. Must be authorized to work in the U.S.",
            },
            {
                "category": "fellowship",
                "title": "York College CISE Student Scholars Program (2027 Cohort)",
                "organization": "York College / Yeshiva University",
                "description": "An NSF-funded research program in Cybersecurity, AI, and IoT. Includes a $1,000 stipend and hands-on lab work at Yeshiva University in NYC.",
                "url": "https://www.york.cuny.edu/mathematics-computer-science/cise",
                "deadline": "2026-10-31",
                "eligibility": "York College Juniors/Seniors, GPA 2.75+, CS/Information Management Systems/Cybersecurity majors or minors.",
            },
            {
                "category": "fellowship",
                "title": "Code2Career",
                "organization": "Project Basta",
                "description": "Technical training and a 10-week mentorship from a Google Software Engineer. Past participants have landed roles at Bloomberg, Amazon, IBM, Nomura, LinkedIn, and more.",
                "url": "https://www.projectbasta.com/code2career",
                "deadline": "2026-09-11",
                "eligibility": "CS majors graduating Fall '26 through Fall '28. Must have completed Seekr.",
            },
            {
                "category": "fellowship",
                "title": "AI Societal Impact Lab - Autumn 2026 Fellowship",
                "organization": "AI Societal Impact Lab",
                "description": "A free, fully remote fellowship exploring the societal, ethical, and governance implications of AI. Runs 8-10 weeks, about 4 hours/week.",
                "url": "https://www.aisocietalimpactlab.com/fellowship-autumn-2026",
                "deadline": "2026-09-04",
                "eligibility": "Open to students and recent graduates from any background.",
            },
            {
                "category": "fellowship",
                "title": "Anthropic Fellows Program",
                "organization": "Anthropic",
                "description": "A fully funded AI safety research fellowship. No PhD, prior ML experience, or published papers required.",
                "url": "https://alignment.anthropic.com/2025/anthropic-fellows-program-2026/",
                "deadline": None,
                "eligibility": "Strong quantitative background (math, CS, physics, or related); rolling for cohorts starting September 2026+.",
            },
            {
                "category": "job",
                "title": "MTA Emerging Talent Virtual Information Session (CUNY-Exclusive)",
                "organization": "Metropolitan Transportation Authority",
                "description": "A virtual info session exclusively for Brooklyn College, York College, and John Jay College students, covering MTA hiring, internship pathways, and a live Q&A with MTA recruiters.",
                "url": "https://mta.zoomgov.com/meeting/register/hjLKtrS1TuqHDw-kPBNZLw",
                "deadline": "2026-10-20",
                "eligibility": "Valid CUNY email and EMPLID required to register.",
            },
            {
                "category": "job",
                "title": "American Express Undergraduate Multi-School Event",
                "organization": "American Express",
                "description": "An invitation-only, half-day in-person look inside American Express - networking, career talks, and exploration of Strategy & Analytics, Tech, Product, Marketing, and more.",
                "url": "https://egug.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26012104",
                "deadline": "2026-09-10",
                "eligibility": "Full-time Bachelor's students graduating December 2027-June 2028.",
            },
            {
                "category": "ctf",
                "title": "PatriotCTF 2026",
                "organization": "Competitive Cyber at Mason",
                "description": "A beginner-friendly Capture The Flag competition hosted by George Mason University's cybersecurity club.",
                "url": "https://pctf.competitivecyber.club/",
                "deadline": "2026-09-11",
                "eligibility": "Open to all students and skill levels.",
            },
            {
                "category": "ctf",
                "title": "NullOrigin CTF Qualifiers",
                "organization": "Cyber HX",
                "description": "A 12-hour international online CTF qualifier.",
                "url": "https://nullorigin.cyberhx.com/",
                "deadline": "2026-09-18",
                "eligibility": "Open to all students and skill levels.",
            },
        ]

        added_opps = 0
        for item in new_opportunities:
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
            added_opps += 1

        new_events = [
            {
                "title": "Build It, Break It, Secure It: The Chatbot Workshop",
                "event_date": "Late September/Early October 2026 (TBD)",
                "time_display": "TBD",
                "location": "York College",
                "description": "Build your own AI chatbot from the ground up - then try to break it. Learn real prompt injection attacks firsthand, then flip roles in a red team/blue team exercise, patching the vulnerability you just exploited.",
                "event_type": "workshop",
            },
            {
                "title": "The Rogue AI Recovery: CYAI's Fall CTF",
                "event_date": "October 2026 (TBD)",
                "time_display": "TBD",
                "location": "York College",
                "description": "A rogue AI has infiltrated York's network - work through live challenges in web exploitation, forensics, OSINT, and password cracking on a real-time scoreboard.",
                "event_type": "ctf",
            },
            {
                "title": "AI on Trial: An Ethics Debate Night",
                "event_date": "October 2026 (TBD)",
                "time_display": "TBD",
                "location": "York College, Business & Econ Conference Room 2B06",
                "description": "A campus-wide, open-floor debate on AI in the classroom, the ethics of AI systems, and where regulation should draw the line. Light bites included.",
                "event_type": "social",
            },
            {
                "title": "Inside Cisco: A Look at Tomorrow's Smart Office",
                "event_date": "November/December 2026 (TBD)",
                "time_display": "TBD",
                "location": "Cisco PENN1, NYC",
                "description": "Step inside Cisco's flagship NYC smart-office space and see enterprise technology in action - connect directly with people building careers in the field.",
                "event_type": "field_trip",
            },
        ]

        added_events = 0
        for item in new_events:
            exists = db.query(models.Event).filter(models.Event.title == item["title"]).first()
            if exists:
                continue
            db.add(models.Event(**item))
            added_events += 1

        db.commit()
        return {"added_opportunities": added_opps, "added_events": added_events}
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

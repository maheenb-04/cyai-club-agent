from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.database import engine, Base
from app import models
from app.routers import opportunities, curated_sources, members, newsletters, events, social_posts
from app.core.security import verify_api_key
from app.core.limiter import limiter

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CYAI Club Assistant Agent")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(opportunities.router, dependencies=[Depends(verify_api_key)])
app.include_router(curated_sources.router, dependencies=[Depends(verify_api_key)])
app.include_router(members.router)
app.include_router(newsletters.router, dependencies=[Depends(verify_api_key)])
app.include_router(events.router, dependencies=[Depends(verify_api_key)])
app.include_router(social_posts.router, dependencies=[Depends(verify_api_key)])


@app.get("/")
def health_check():
    return {"status": "ok", "service": "cyai-club-agent"}

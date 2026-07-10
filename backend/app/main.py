from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app import models
from app.routers import opportunities

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CYAI Club Assistant Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(opportunities.router)
@app.get("/")
def health_check():
    return {"status": "ok", "service": "cyai-club-agent"}
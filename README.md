# CYAI Club Assistant Agent

An AI-powered assistant built for a college Cybersecurity & AI club to automate the discovery, curation, and distribution of career opportunities, scholarships, and club communications — so student leaders can spend less time searching and more time building community.

## What It Does

The agent continuously discovers and curates real, current opportunities relevant to undergraduate students in cybersecurity and AI, then turns that data into ready-to-use newsletters and social content — all reviewed by a human before anything goes out.

### Core Features

**Opportunity Aggregation**
- Live CTF competition tracking (CTFtime)
- Entry-level job and internship sourcing (Adzuna), filtered specifically for students with no professional experience
- AI-assisted discovery of scholarships, fellowships, tech-prep programs, and residency programs (Tavily search + Mistral AI extraction and validation)
- Automatic dead-link detection and cleanup
- Automatic removal of opportunities past their deadline

**Newsletter Generation**
- AI-drafted monthly newsletters matching the club's real editorial voice
- Avoids repeating the same opportunities across consecutive newsletters
- Full review-and-edit workflow before anything is sent
- Branded PDF export with QR codes linking directly to each opportunity

**Social Media Content**
- Auto-generated CircleIn and Instagram post drafts from any opportunity or event
- Manual "write your own" option for fully custom posts
- Every post is a draft — nothing posts automatically

**Club Operations**
- Event management with photo/flyer uploads
- Member list management with self-serve unsubscribe
- CSV export for backups and reporting
- System health dashboard for monitoring integrations

**Automation, With Guardrails**
- Scheduled background sync for fresh opportunities (daily) and AI-powered searches (weekly)
- All content generation stops short of the final send/post — a human always reviews before anything reaches real people

## How It's Built

**Backend:** FastAPI (Python), PostgreSQL (hosted on Supabase), SQLAlchemy ORM, APScheduler for background jobs, Playwright for PDF rendering, rate limiting and API-key authentication throughout.

**Frontend:** React + Vite + Tailwind CSS, a custom dashboard for club officers to manage everything the agent tracks.

**AI Integrations:** Mistral AI for content generation and extraction, Tavily for web search.

## Project History

This project started as a fully local tool — a FastAPI backend and React frontend running entirely on a laptop, used to prototype and validate the core workflows (sourcing, newsletter generation, member management). Once the feature set was proven out, the project was migrated to a cloud-hosted architecture: the database moved to a managed PostgreSQL instance, and the backend and frontend were deployed as separate always-on web services — making the tool accessible to the full club leadership team from any device, without requiring anyone to run code locally.

## Security

- API-key authentication on all administrative endpoints
- Rate limiting on all AI-powered and external-API-calling endpoints
- Automated link validation before any URL is surfaced to members
- No credentials or member data committed to source control
- Content generation and sending are strictly separated — no automated system sends anything to real people without human review

## Status

Actively maintained and used in production by club leadership for opportunity sourcing, monthly newsletters, and event coordination.

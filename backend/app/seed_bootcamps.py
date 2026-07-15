from app.database import SessionLocal
from app import models

BOOTCAMP_RESOURCES = [
    {
        "category": "bootcamp",
        "title": "TryHackMe: Pre Security Path",
        "organization": "TryHackMe",
        "description": (
            "Self-paced, structured learning path covering networking basics, Linux, "
            "how the internet works, and core security concepts. The best starting point "
            "for students who feel like they don't know enough yet - builds the exact "
            "foundation needed for cybersecurity roles and CTF challenges."
        ),
        "url": "https://tryhackme.com/path/outline/presecurity",
        "deadline": None,
        "eligibility": "Open to all skill levels, no application required, self-paced",
        "source": "curated:tryhackme_presecurity",
        "source_type": "curated",
    },
    {
        "category": "bootcamp",
        "title": "Hack The Box: Starting Point Machines",
        "organization": "Hack The Box",
        "description": (
            "Guided, step-by-step hacking labs that feel like real-world cybersecurity work. "
            "Learn how to scan systems, find vulnerabilities, and break into them in a "
            "controlled environment."
        ),
        "url": "https://app.hackthebox.com/starting-point",
        "deadline": None,
        "eligibility": "Open to all skill levels, no application required, self-paced",
        "source": "curated:htb_starting_point",
        "source_type": "curated",
    },
    {
        "category": "bootcamp",
        "title": "Kaggle: Intro to Machine Learning",
        "organization": "Kaggle",
        "description": (
            "Hands-on course teaching how to train models and work with real datasets. "
            "One of the easiest ways to start learning AI/ML - teaches how machine "
            "learning actually works, not just theory."
        ),
        "url": "https://www.kaggle.com/learn/intro-to-machine-learning",
        "deadline": None,
        "eligibility": "Open to all skill levels, no application required, self-paced",
        "source": "curated:kaggle_intro_ml",
        "source_type": "curated",
    },
    {
        "category": "bootcamp",
        "title": "Google AI: Machine Learning Crash Course",
        "organization": "Google",
        "description": (
            "Structured, interactive course covering core ML concepts with exercises and "
            "real examples. Good for strengthening fundamentals before taking higher-level "
            "AI courses."
        ),
        "url": "https://developers.google.com/machine-learning/crash-course",
        "deadline": None,
        "eligibility": "Open to all skill levels, no application required, self-paced",
        "source": "curated:google_ml_crash_course",
        "source_type": "curated",
    },
]

FELLOWSHIP_SOURCES_TO_TRACK = [
    {
        "name": "Heron AI Security Research Fellowship",
        "url": "https://www.edtechinnovationhub.com/news/heron-opens-ai-security-research-fellowship-for-cybersecurity-professionals",
        "category": "fellowship",
        "check_frequency": "quarterly",
        "notes": "Requires 5+ years cybersecurity experience - not currently undergrad-appropriate. Check future cycles in case eligibility changes.",
    },
    {
        "name": "ProFellow AI Fellowships Directory",
        "url": "https://www.profellow.com/fellowships/ai-fellowships/",
        "category": "fellowship",
        "check_frequency": "quarterly",
        "notes": "Aggregates many AI/cybersecurity fellowships - most require grad-level or professional experience. Periodically check for undergrad-eligible ones.",
    },
]


def seed():
    db = SessionLocal()

    added_opps = 0
    skipped_opps = 0
    for item in BOOTCAMP_RESOURCES:
        exists = db.query(models.Opportunity).filter(
            models.Opportunity.source == item["source"]
        ).first()
        if exists:
            skipped_opps += 1
            continue
        db.add(models.Opportunity(**item))
        added_opps += 1

    added_sources = 0
    skipped_sources = 0
    for src in FELLOWSHIP_SOURCES_TO_TRACK:
        exists = db.query(models.CuratedSource).filter(
            models.CuratedSource.url == src["url"]
        ).first()
        if exists:
            skipped_sources += 1
            continue
        db.add(models.CuratedSource(**src))
        added_sources += 1

    db.commit()
    print(f"Bootcamp opportunities: added {added_opps}, skipped {skipped_opps}")
    print(f"Fellowship sources tracked: added {added_sources}, skipped {skipped_sources}")
    db.close()


if __name__ == "__main__":
    seed()

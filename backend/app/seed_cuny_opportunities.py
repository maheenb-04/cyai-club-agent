from app.database import SessionLocal
from app import models

CUNY_OPPORTUNITIES = [
    {
        "category": "internship",
        "title": "CUNY Career Launch",
        "organization": "CUNY",
        "description": (
            "Paid internships across many fields including tech and cybersecurity, "
            "open to current CUNY undergraduate students. Priority deadline typically "
            "in mid-February; check site for current cycle dates."
        ),
        "url": "https://www.cuny.edu/about/administration/offices/ocip/students/careerlaunch/",
        "deadline": None,
        "eligibility": "Current CUNY undergraduate students, actively enrolled in matriculated courses",
        "source": "cuny:career_launch",
        "source_type": "curated",
    },
    {
        "category": "internship",
        "title": "CUNY Spring Forward",
        "organization": "CUNY",
        "description": (
            "Paid spring internships for CUNY undergrads with no prior paid internship "
            "experience. Includes a STEM hub track. No age cap (18+), priority given to "
            "freshmen and sophomores. Minimum 2.0 GPA required."
        ),
        "url": "https://www.cuny.edu/about/administration/offices/ocip/students/spring-forward/",
        "deadline": None,
        "eligibility": "CUNY undergrads, 18+, GPA 2.0+, no prior paid internship experience",
        "source": "cuny:spring_forward",
        "source_type": "curated",
    },
    {
        "category": "internship",
        "title": "CUNY Internship Programs (NYC Agency Partnerships)",
        "organization": "CUNY / NYC Agencies",
        "description": (
            "Internships and post-graduate fellowships in tech, engineering, and other "
            "sectors, in partnership with NYC agencies. Apply via your campus Handshake "
            "platform using your CUNY email."
        ),
        "url": "https://www.cuny.edu/employment/student-jobs/internships/cuny-internship-programs/",
        "deadline": None,
        "eligibility": "Current CUNY students, apply through campus Handshake account",
        "source": "cuny:internship_programs",
        "source_type": "curated",
    },
    {
        "category": "internship",
        "title": "NYC Office of Technology and Innovation (OTI) Internships",
        "organization": "NYC Office of Technology and Innovation",
        "description": (
            "City government technology internships through NYC's OTI office. "
            "Relevant for students interested in public-sector IT and cybersecurity work."
        ),
        "url": "https://www.nyc.gov/content/oti/pages/internships",
        "deadline": None,
        "eligibility": "Check current posting for specific eligibility",
        "source": "cuny:nyc_oti",
        "source_type": "curated",
    },
]


def seed():
    db = SessionLocal()
    added = 0
    skipped = 0

    for item in CUNY_OPPORTUNITIES:
        exists = db.query(models.Opportunity).filter(
            models.Opportunity.source == item["source"]
        ).first()
        if exists:
            skipped += 1
            continue

        db_opportunity = models.Opportunity(**item)
        db.add(db_opportunity)
        added += 1

    db.commit()
    print(f"Added {added}, skipped {skipped} duplicates")
    db.close()


if __name__ == "__main__":
    seed()
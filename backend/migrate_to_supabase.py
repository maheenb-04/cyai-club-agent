from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app import models

sqlite_engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SqliteSession = sessionmaker(bind=sqlite_engine)

pg_url = settings.supabase_database_url.replace("postgresql://", "postgresql+psycopg://")
pg_engine = create_engine(pg_url)
PgSession = sessionmaker(bind=pg_engine)

MODELS_IN_ORDER = [
    models.Member,
    models.Opportunity,
    models.Event,
    models.CuratedSource,
    models.Newsletter,
    models.NewsletterOpportunity,
    models.SocialPost,
]


def migrate():
    sqlite_db = SqliteSession()
    pg_db = PgSession()

    try:
        for model in MODELS_IN_ORDER:
            rows = sqlite_db.query(model).all()
            table_name = model.__tablename__
            print(f"Migrating {table_name}: {len(rows)} rows")

            for row in rows:
                data = {c.name: getattr(row, c.name) for c in model.__table__.columns}
                pg_db.execute(model.__table__.insert().values(**data))

            pg_db.commit()

            seq_name = f"{table_name}_id_seq"
            pg_db.execute(text(
                f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table_name}), 1))"
            ))
            pg_db.commit()

        print("Migration complete!")

    finally:
        sqlite_db.close()
        pg_db.close()


if __name__ == "__main__":
    migrate()

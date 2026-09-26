from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Fix schema prefix for postgres if needed (PostgreSQL 14+ / SQLAlchemy compatibility)
db_url = settings.DATABASE_URL
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Create engine with connection resilience for cloud PostgreSQL / Supabase pooler
engine_kwargs = {"pool_pre_ping": True}
if not db_url.startswith("sqlite"):
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

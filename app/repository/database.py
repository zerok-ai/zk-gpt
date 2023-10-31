from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import config

postgres_host = config.configuration.get("postgres_host", "localhost")
postgres_port = config.configuration.get("postgres_port", "5432")
postgres_db = config.configuration.get("postgres_db", "gpt")
postgres_user = config.configuration.get("postgres_user", "postgres")
postgres_pass = config.configuration.get("postgres_pass", "eo1Mgtm6HI")

DATABASE_URL = f"postgresql://{postgres_user}:{postgres_pass}@{postgres_host}/{postgres_db}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()


def get_db():
    try:
        yield db
    finally:
        db.close()

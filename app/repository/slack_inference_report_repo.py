from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.db import SlackInferenceReportSQL
from app.models.models import SlackInferenceReport

app = FastAPI()

# Set up SQLAlchemy database connection
DATABASE_URL = "postgresql://username:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Define the get_db dependency function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Route using Pydantic model
@app.post("/create_report/", response_model=SlackInferenceReport)
def create_report(report: SlackInferenceReport, db: Session = Depends(get_db)):
    db_report = SlackInferenceReportSQL(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

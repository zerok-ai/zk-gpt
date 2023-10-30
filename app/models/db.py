from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class SlackInferenceReportSQL(Base):
    __tablename__ = 'slack_inference_report'

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String, nullable=False)
    incident_id = Column(String, nullable=False)
    reporting_status = Column(Boolean)
    issue_timestamp = Column(TIMESTAMP)
    report_timestamp = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)
    clear_reporting_timestamp = Column(TIMESTAMP)
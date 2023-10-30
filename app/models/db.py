from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SlackInferenceReportDB(Base):
    __tablename__ = 'slack_inference_report'

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String, nullable=False)
    incident_id = Column(String, nullable=False)
    reporting_status = Column(Boolean)
    issue_timestamp = Column(TIMESTAMP)
    report_timestamp = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)
    clear_reporting_timestamp = Column(TIMESTAMP)

    # Ensure unique constraint for issue_id and incident_id
    __table_args__ = (
        UniqueConstraint('issue_id', 'incident_id', name='unique_slack_incident_context'),
    )


class IssueIncidentContextDB(Base):
    __tablename__ = 'issue_incident_context'

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String(255), nullable=False)
    incident_id = Column(String(255), nullable=False)
    context = Column(BYTEA)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    # Ensure unique constraint for issue_id and incident_id
    __table_args__ = (
        UniqueConstraint('issue_id', 'incident_id', name='unique_issue_incident_context'),
    )


class IssueIncidentInferenceDB(Base):
    __tablename__ = 'issue_incident_inference'

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String(255), nullable=False)
    incident_id = Column(String(255), nullable=False)
    issue_title = Column(String(255))
    inference = Column(BYTEA)
    created_at = Column(TIMESTAMP)
    issue_last_seen = Column(TIMESTAMP)
    issue_first_seen = Column(TIMESTAMP)

    # Ensure unique constraint for issue_id and incident_id
    __table_args__ = (
        UniqueConstraint('issue_id', 'incident_id', name='unique_issue_incident_inference'),
    )


class IssueUserConversationEventDB(Base):
    __tablename__ = 'issue_user_conversation_events'

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String(255), nullable=False, index=True)
    incident_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(255), nullable=False)
    event_request = Column(BYTEA)
    event_response = Column(BYTEA)
    created_at = Column(TIMESTAMP)

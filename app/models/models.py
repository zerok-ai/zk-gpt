from pydantic import BaseModel
from datetime import datetime


class SlackInferenceReport(BaseModel):
    issue_id: str
    incident_id: str
    reporting_status: bool
    issue_timestamp: datetime
    report_timestamp: datetime
    created_at: datetime
    clear_reporting_timestamp: datetime

    class Config:
        orm_mode = True


class IssueIncidentContextCreate(BaseModel):
    issue_id: str
    incident_id: str
    context: bytes

    class Config:
        orm_mode = True


class IssueIncidentContext(BaseModel):
    issue_id: str
    incident_id: str
    context: bytes
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class IssueIncidentInference(BaseModel):
    issue_id: str
    incident_id: str
    issue_title: str
    inference: str
    created_at: datetime
    issue_last_seen: datetime
    issue_first_seen: datetime

    class Config:
        orm_mode = True

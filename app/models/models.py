from pydantic import BaseModel
from datetime import datetime


class SlackInferenceReport(BaseModel):
    id: int
    issue_id: str
    incident_id: str
    reporting_status: bool
    issue_timestamp: datetime
    report_timestamp: datetime
    created_at: datetime
    clear_reporting_timestamp: datetime

    class Config:
        orm_mode = True




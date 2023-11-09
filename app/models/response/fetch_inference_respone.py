import json
from typing import Optional

from pydantic import BaseModel


class InferenceSummaryAnomaly(BaseModel):
    summary: Optional[str] = None
    anomalies: Optional[str] = None
    data: str

    def to_dict(self):
        data_dict = {
            "summary": self.summary,
            "anomalies": self.anomalies,
            "data": self.data  # Convert str to JSON string
        }
        return data_dict


class FetchInferenceResponse(BaseModel):
    issueId: str
    incidentId: str
    inference: InferenceSummaryAnomaly

    def to_dict(self):
        return self.model_dump()


class FetchInferenceResponseDashboard(BaseModel):
    payload: FetchInferenceResponse

    def to_dict(self):
        return self.model_dump()


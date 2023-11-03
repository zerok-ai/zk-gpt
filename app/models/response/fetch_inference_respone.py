from pydantic import BaseModel

from app.models.response.generic_response import GenericResponseInterface


class InferenceSummaryAnomaly(BaseModel):
    summary: str | None
    anomalies: str | None
    data: str

    def to_dict(self):
        return self.model_dump()


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


from pydantic import BaseModel

from app.models.response.gereric_respone import GenericResponseInterface


class InferenceSummaryAnomaly(BaseModel):
    summary: str | None
    anomalies: str | None
    data: str


class FetchInferenceResponse(GenericResponseInterface):
    issueId: str
    incidentId: str
    inference: InferenceSummaryAnomaly

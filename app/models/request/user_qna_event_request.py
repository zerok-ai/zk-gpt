from pydantic import BaseModel
from typing import Any, Dict


class UserQnaEvent(BaseModel):
    request:  Dict[str, Any]
    type: str

    def to_dict(self):
        return self.model_dump()


class UserQnaEventRequest(BaseModel):
    issueId: str
    incidentId: str
    event: UserQnaEvent

    def to_dict(self):
        return self.model_dump()
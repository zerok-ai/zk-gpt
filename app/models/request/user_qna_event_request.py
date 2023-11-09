from pydantic import BaseModel
from typing import Any, Dict, Optional


class UserQnaEvent(BaseModel):
    request: Optional[Dict[str, Any]] = None
    type: str

    def to_dict(self):
        return self.model_dump()


class UserQnaEventRequest(BaseModel):
    issueId: str
    incidentId: str
    event: UserQnaEvent

    def to_dict(self):
        return self.model_dump()
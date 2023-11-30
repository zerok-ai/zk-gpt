from typing import Optional

from pydantic import BaseModel


class PromCustomMetricDataRequest(BaseModel):
    query: str
    time: Optional[int] = None
    duration: Optional[str] = None
    step: Optional[str] = None

    def to_dict(self):
        req_dict = {
            "query": self.query,
            "time": self.time,
            "duration": self.duration,
            "step": self.step
        }
        return req_dict

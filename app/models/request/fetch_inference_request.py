from pydantic import BaseModel
from typing import Any, Dict


class FetchInferenceRequest(BaseModel):
    data: Dict[str, Any]
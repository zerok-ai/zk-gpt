from pydantic import BaseModel
from typing import Any, Dict


class GenericRequest(BaseModel):
    data: Dict[str, Any]
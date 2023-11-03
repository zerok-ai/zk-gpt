from app.models.response.generic_response import GenericResponseInterface


class IncidentRcaResponse(GenericResponseInterface):
    rca: str

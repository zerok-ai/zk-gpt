from app.models.response.gereric_respone import GenericResponseInterface


class IncidentRcaResponse(GenericResponseInterface):
    rca: str

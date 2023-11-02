from pydantic import BaseModel


class GenericResponseInterface(BaseModel):
    pass


class GenericResponse(BaseModel):
    payload: GenericResponseInterface

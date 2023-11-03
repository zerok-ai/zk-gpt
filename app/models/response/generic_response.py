from pydantic import BaseModel


class GenericResponseInterface(BaseModel):
    pass

    def to_dict(self):
        return self.model_dump()


class GenericResponse(BaseModel):
    payload: GenericResponseInterface

    def to_dict(self):
        return self.model_dump()


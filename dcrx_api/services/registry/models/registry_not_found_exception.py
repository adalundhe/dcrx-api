from pydantic import BaseModel, StrictStr


class RegistryNotFoundException(BaseModel):
    message: StrictStr
import uuid
from pydantic import (
    BaseModel,
    StrictStr
)


class Registry(BaseModel):
    id: uuid.UUID
    registry_name: StrictStr
    registry_uri: StrictStr
    registry_user: StrictStr
    registry_password: StrictStr

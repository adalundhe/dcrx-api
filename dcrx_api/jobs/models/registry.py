from pydantic import (
    BaseModel,
    StrictStr
)


class Registry(BaseModel):
    registry_uri: StrictStr
    registry_user: StrictStr
    registry_password: StrictStr

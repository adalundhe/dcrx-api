from pydantic import (
    BaseModel,
    StrictStr
)


class RegistryMetadata(BaseModel):
    registry_name: StrictStr
    registry_uri: StrictStr
    registry_user: StrictStr
    registry_password: StrictStr

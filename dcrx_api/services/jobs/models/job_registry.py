from pydantic import (
    BaseModel,
    StrictStr
)


class JobRegistry(BaseModel):
    registry_name: StrictStr
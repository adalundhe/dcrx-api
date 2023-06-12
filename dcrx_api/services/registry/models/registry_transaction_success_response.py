import uuid
from pydantic import (
    BaseModel,
    StrictStr
)
from typing import Optional


class RegistryTransactionSuccessResponse(BaseModel):
    id: uuid.UUID
    registry_name: Optional[StrictStr]
    message: Optional[StrictStr]
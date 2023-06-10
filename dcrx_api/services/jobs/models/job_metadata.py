import uuid
from pydantic import (
    BaseModel,
    StrictStr,
    StrictInt
)


class JobMetadata(BaseModel):
    id: uuid.UUID
    name: StrictStr
    image: StrictStr
    tag: StrictStr
    status: StrictStr
    context: StrictStr
    size: StrictInt=0

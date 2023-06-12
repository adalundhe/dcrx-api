import uuid
from pydantic import (
    BaseModel,
    StrictStr,
    StrictInt,
    HttpUrl
)


class JobMetadata(BaseModel):
    id: uuid.UUID
    image_registry: HttpUrl
    name: StrictStr
    image: StrictStr
    tag: StrictStr
    status: StrictStr
    context: StrictStr
    size: StrictInt=0

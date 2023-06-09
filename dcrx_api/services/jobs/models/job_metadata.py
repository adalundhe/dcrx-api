import uuid
from pydantic import (
    BaseModel,
    StrictStr
)


class JobMetadata(BaseModel):
    id: uuid.UUID
    name: StrictStr
    image: StrictStr
    tag: StrictStr
    status: StrictStr
    context: StrictStr

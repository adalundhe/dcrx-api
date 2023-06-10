from pydantic import (
    BaseModel,
    StrictFloat,
    StrictStr
)


class ServerMemoryLimitException(BaseModel):
    message: StrictStr
    limit: StrictFloat
    current: StrictFloat
from pydantic import (
    BaseModel,
    StrictInt,
    StrictFloat
)


class ImageStats(BaseModel):
    size: StrictInt=0
from pydantic import (
    BaseModel,
    StrictBool
)


class BuildOptions(BaseModel):
    nocache: StrictBool=False
from pydantic import (
    BaseModel,
    StrictStr
)
from typing import Optional


class JobStepResult(BaseModel):
    message: StrictStr
    error: Optional[StrictStr]
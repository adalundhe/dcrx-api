import uuid
from pydantic import BaseModel, StrictStr


class JobNotFoundException(BaseModel):
    job_id: uuid.UUID
    message: StrictStr
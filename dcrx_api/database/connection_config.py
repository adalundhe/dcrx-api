from pydantic import (
    BaseModel,
    StrictStr
)
from typing import Literal, Optional

class ConnectionConfig(BaseModel):
    database_username: Optional[StrictStr]
    database_password: Optional[StrictStr]
    database_type: Literal['mysql', 'asyncpg', 'sqlite']
    database_uri: StrictStr
    database_name: Optional[StrictStr]

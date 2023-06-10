from pydantic import (
    BaseModel,
    StrictStr,
    StrictInt
)
from typing import Literal, Optional

class ConnectionConfig(BaseModel):
    database_username: Optional[StrictStr]
    database_password: Optional[StrictStr]
    database_type: Literal['mysql', 'asyncpg', 'sqlite']
    database_uri: StrictStr
    database_port: Optional[StrictInt]
    database_name: Optional[StrictStr]

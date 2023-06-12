import psutil
from pydantic import (
    BaseModel,
    StrictStr,
    StrictInt,
    StrictFloat
)
from typing import (
    Optional, 
    Dict, 
    Union,
    Callable
)


PrimaryType = Union[str, int, float, bytes, bool]


class Env(BaseModel):
    DCRX_API_MAX_MEMORY_PERCENT_USAGE: StrictFloat=50
    DCRX_API_JOB_TIMEOUT: StrictStr='5s'
    DCRX_API_JOB_PRUNE_INTERVAL: StrictStr='1s'
    DCRX_API_JOB_MAX_AGE: StrictStr='1m'
    DCRX_API_JOB_WORKERS: StrictInt=psutil.cpu_count()
    DCRX_API_JOB_POOL_SIZE: StrictInt=10
    DCRX_API_SECRET_KEY: StrictStr
    DCRX_API_AUTH_ALGORITHM: StrictStr='HS256'
    DCRX_API_TOKEN_EXPIRATION: StrictStr='15m'
    DCRX_API_DATABASE_TYPE: Optional[StrictStr]='sqlite'
    DCRX_API_DATABASE_USER: Optional[StrictStr]
    DCRX_API_DATABASE_URI: Optional[StrictStr]
    DCRX_API_DATABASE_PORT: Optional[StrictInt]
    DCRX_API_DATABASE_PASSWORD: Optional[StrictStr]
    DCRX_API_DATABASE_NAME: StrictStr='dcrx'

    @classmethod
    def types_map(self) -> Dict[str, Callable[[str], PrimaryType]]:
        return {
            'DCRX_API_MAX_MEMORY_PERCENT_USAGE': float,
            'DCRX_API_JOB_PRUNE_INTERVAL': str,
            'DCRX_API_JOB_TIMEOUT': str,
            'DCRX_API_JOB_MAX_AGE': str,
            'DCRX_API_JOB_WORKERS': int,
            'DCRX_API_JOB_POOL_SIZE': int,
            'DCRX_API_SECRET_KEY': str,
            'DCRX_API_AUTH_ALGORITHM': str,
            'DCRX_API_TOKEN_EXPIRATION': str,
            'DCRX_API_DATABASE_TYPE': str,
            'DCRX_API_DATABASE_USER': str,
            'DCRX_API_DATABASE_PASSWORD': str,
            'DCRX_API_DATABASE_NAME': str,
            'DCRX_API_DATABASE_URI': str,
            'DCRX_API_DATABASE_PORT': int
        }
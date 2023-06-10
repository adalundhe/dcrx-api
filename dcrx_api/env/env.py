import psutil
from pydantic import (
    BaseModel,
    StrictStr,
    StrictInt
)
from typing import (
    Optional, 
    Dict, 
    Union,
    Callable
)


PrimaryType = Union[str, int, float, bytes, bool]


class Env(BaseModel):
    DCRX_API_WORKERS: StrictInt=psutil.cpu_count()
    DCRX_API_SECRET_KEY: StrictStr
    DCRX_API_AUTH_ALGORITHM: StrictStr='HS256'
    DCRX_API_TOKEN_EXPIRATION_MINUTES: StrictInt=30
    DCRX_API_DATABASE_TYPE: Optional[StrictStr]='sqlite'
    DCRX_API_DATABASE_USER: Optional[StrictStr]
    DCRX_API_DATABASE_URI: StrictStr
    DCRX_API_DATABASE_PASSWORD: Optional[StrictStr]
    DCRX_API_DATABASE_NAME: StrictStr='dcrx'
    DOCKER_REGISTRY_URI: StrictStr
    DOCKER_REGISTRY_USERNAME: StrictStr
    DOCKER_REGISTRY_PASSWORD: StrictStr

    @classmethod
    def types_map(self) -> Dict[str, Callable[[str], PrimaryType]]:
        return {
            'DCRX_API_WORKERS': int,
            'DCRX_API_SECRET_KEY': str,
            'DCRX_API_AUTH_ALGORITHM': str,
            'DCRX_API_TOKEN_EXPIRATION_MINUTES': int,
            'DCRX_API_DATABASE_TYPE': str,
            'DCRX_API_DATABASE_USER': str,
            'DCRX_API_DATABASE_PASSWORD': str,
            'DCRX_API_DATABASE_NAME': str,
            'DCRX_API_DATABASE_URI': str,
            'DOCKER_REGISTRY_URI': str,
            'DOCKER_REGISTRY_USERNAME': str,
            'DOCKER_REGISTRY_PASSWORD': str
        }
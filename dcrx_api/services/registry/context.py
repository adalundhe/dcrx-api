from dcrx_api.context.types import ContextType
from dcrx_api.env import Env
from pydantic import BaseModel
from .connection import RegistryConnection



class RegistryServiceContext(BaseModel):
    env: Env
    connection: RegistryConnection
    context_type: ContextType=ContextType.REGISTRY_SERVICE


    class Config:
        arbitrary_types_allowed = True

    async def initialize(self):
        await self.connection.connect()
        await self.connection.init()

    async def close(self):
        await self.connection.close()
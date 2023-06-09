from dcrx_api.context.types import ContextType
from dcrx_api.env import Env
from pydantic import BaseModel
from .queue import JobQueue
from .connection import JobsConnection



class JobServiceContext(BaseModel):
    env: Env
    queue: JobQueue
    connection: JobsConnection
    context_type: ContextType=ContextType.JOB_SERVICE


    class Config:
        arbitrary_types_allowed = True

    async def initialize(self):
        await self.connection.connect()
        await self.connection.init()

    async def close(self):
        await self.queue.close()
        await self.connection.close()
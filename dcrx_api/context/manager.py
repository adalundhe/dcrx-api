from dcrx_api.services.auth.context import AuthServiceContext
from dcrx_api.services.jobs.context import JobServiceContext
from dcrx_api.services.users.context import UsersServiceContext
from typing import Dict, Union, List
from .types import ContextType


class ContextManager:

    def __init__(self) -> None:
        self.contexts: Dict[
            ContextType, 
            Union[
                AuthServiceContext,
                JobServiceContext, 
                UsersServiceContext
            ]
        ] = {}

    
    def get(self, context_type: ContextType) -> Union[
        AuthServiceContext,
        JobServiceContext,
        UsersServiceContext,
        None
    ]:
        return self.contexts.get(context_type)

    async def initialize(
        self,
        contexts: List[
            Union[
                AuthServiceContext,
                JobServiceContext,
                UsersServiceContext
            ]
        ]
    ):
        
        for context in contexts:
            await context.initialize()
            self.contexts[context.context_type] = context

    async def close(self):
        for context in self.contexts.values():
            await context.close()
        


context = ContextManager()
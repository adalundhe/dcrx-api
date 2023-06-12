from dcrx_api.database import (
    DatabaseConnection,
    ConnectionConfig
)
from dcrx_api.database.models import DatabaseTransactionResult
from dcrx_api.env import Env
from typing import (
    List,
    Dict,
    Any
)
from .models import Registry
from .table import RegistryTable


class RegistryConnection(DatabaseConnection[Registry]):

    def __init__(self, env: Env) -> None:
        super().__init__(
            ConnectionConfig(
                database_username=env.DCRX_API_DATABASE_USER,
                database_password=env.DCRX_API_DATABASE_PASSWORD,
                database_type=env.DCRX_API_DATABASE_TYPE,
                database_uri=env.DCRX_API_DATABASE_URI,
                database_port=env.DCRX_API_DATABASE_PORT,
                database_name=env.DCRX_API_DATABASE_NAME,
                database_transaction_retries=env.DCRX_API_DATABASE_TRANSACTION_RETRIES
            )
        )

        self.table: RegistryTable[Registry] = RegistryTable(
            'registries',
            database_type=self.config.database_type
        )

    async def init(self) -> DatabaseTransactionResult[Registry]:
        return await self.create_table(self.table.selected.table)

    async def select(
        self, 
        filters: Dict[str, Any]={}
    ) -> DatabaseTransactionResult[Registry]:
        return await self.get(
            self.table.select(
                filters={
                    name: self.table.selected.types_map.get(
                        name
                    )(value) for name, value in filters.items()
                }
            )
        )

    async def create(
        self, 
        registries: List[Registry]
    ) -> DatabaseTransactionResult[Registry]:
       return await self.insert_or_update(
           self.table.insert(registries)
       )
    
    async def update(
        self, 
        registries: List[Registry],
        filters: Dict[str, Any]={}
    ) -> DatabaseTransactionResult[Registry]:
        return await self.insert_or_update(
            self.table.update(
                registries,
                filters={
                    name: self.table.selected.types_map.get(
                        name
                    )(value) for name, value in filters.items()
                }
            )
        )
    
    async def remove(
        self,
        filters: Dict[str, Any]
    ) -> DatabaseTransactionResult[Registry]:
        return await self.delete([
            self.table.delete({
                name: self.table.selected.types_map.get(
                    name
                )(value) for name, value in filters.items()
            })
        ])
    
    async def drop(self) -> DatabaseTransactionResult[Registry]:
        return await self.drop_table(self.table)
    

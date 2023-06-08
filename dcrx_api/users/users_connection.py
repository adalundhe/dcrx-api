from dcrx_api.database import (
    DatabaseConnection,
    ConnectionConfig
)
from typing import (
    List,
    Dict,
    Any
)
from .models import DBUser
from .table import UsersTable


class UsersConnection(DatabaseConnection[DBUser]):

    def __init__(self, config: ConnectionConfig) -> None:
        super().__init__(config)
        self.table: UsersTable[DBUser] = UsersTable(
            'users',
            database_type=config.database_type
        )

    async def create_table(self):
        return await super().create_table(self.table.selected.table)

    async def select(
        self, 
        filters: Dict[str, Any]={}
    ):
        return await super().get(
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
        users: List[DBUser]
    ):
       return await super().insert_or_update(
           self.table.insert(users)
       )
    
    async def update(
        self, 
        users: List[DBUser],
        filters: Dict[str, Any]={}
    ):
        return await super().insert_or_update(
            self.table.update(
                users,
                filters={
                    name: self.table.selected.types_map.get(
                        name
                    )(value) for name, value in filters.items()
                }
            )
        )
    
    async def delete(
        self,
        filters: Dict[str, Any]
    ):
        return await super().delete(
            self.table.delete({
                name: self.table.selected.types_map.get(
                    name
                )(value) for name, value in filters.items()
            })
        )
    
    async def drop_table(self):
        return await super().drop_table(self.table)
    

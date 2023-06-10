import asyncio
from sqlalchemy import Table
from sqlalchemy.sql import (
    Select,
    Insert,
    Update,
    Delete
)
from sqlalchemy.schema import (
    CreateTable, 
    DropTable
)
from aiomysql.sa.engine import Engine as MySQLEngine
from aiomysql.sa import create_engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine as PostgresEngine,
    AsyncConnection
)
from typing import (
    Union, 
    Generic,
    TypeVar,
    List
)
from .connection_config import ConnectionConfig


T = TypeVar('T')


class DatabaseConnection(Generic[T]):

    def __init__(self, config: ConnectionConfig) -> None:
        
        self.config = config

        self.engine: Union[
            MySQLEngine,
            PostgresEngine,
            None
        ] = None

        self.connection: Union[
            AsyncConnection,
            None
        ] = None

        self.loop: Union[asyncio.AbstractEventLoop, None] = None

    async def connect(self):
        self.loop = asyncio.get_event_loop()

        if self.engine is None and self.config.database_type == 'mysql':
            self.engine = create_engine(
                user=self.config.database_username,
                password=self.config.database_password,
                host=self.config.database_uri,
                database=self.config.database_name,
                loop=self.loop
            )

        elif self.engine is None and self.config.database_type == 'asyncpg':
            
            connection_string = ['postgresql+asyncpg://']
            
            if self.config.database_username and self.config.database_password:
                connection_string.append(
                    f'{self.config.database_username}:{self.config.database_password}@'
                )

            connection_string.append(f'{self.config.database_uri}:5432')

            if self.config.database_name:
                connection_string.append(self.config.database_name)

            connection_string = ''.join(connection_string)

            self.engine = create_async_engine(connection_string)

        elif self.engine is None and self.config.database_type == 'sqlite':
            self.engine = create_async_engine(self.config.database_uri)

        self.connection = await self.engine.connect()

    async def create_table(
        self,
        table: Table
    ):
        await self.connection.execute(
            CreateTable(
                table,
                if_not_exists=True
            )
        )

        await self.connection.commit()

    async def get(
        self, 
        statement: Select
    ) -> List[T]:
        results = await self.connection.execute(statement)
        return [
            row for row in results
        ]
    
    async def insert_or_update(
        self,
        statements: List[
            Union[Insert, Update]
        ]
    ):
        
        for statement in statements:
            await self.connection.execute(statement)
        
        await self.connection.commit()

    async def delete(
        self,
        statements: List[Delete]
    ):

        for statement in statements:
            await self.connection.execute(statement)
        
        await self.connection.commit()

    async def drop_table(
        self,
        table: Table
    ):
        await self.connection.execute(
            DropTable(
                table,
                if_exists=True
            )
        )

        await self.connection.commit()
    
    async def close(self):
        await self.connection.close()

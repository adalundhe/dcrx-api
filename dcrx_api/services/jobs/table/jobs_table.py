from pydantic import BaseModel
from sqlalchemy.sql import (
    Select,
    Insert,
    Update,
    Delete
)
from typing import (
    Literal, 
    Dict, 
    List,
    Any,
    Union,
    Callable,
    Optional,
    TypeVar,
    Generic
)
from .jobs_mysql_table import JobsMySQLTable
from .jobs_postgres_table import JobsPostgresTable
from .jobs_sqlite_table import JobsSQLiteTable

M = TypeVar('M', bound=BaseModel)

class JobsTable(Generic[M]):

    def __init__(
        self,
        users_table_name: str,
        database_type: Literal["mysql", "postgres", "sqlite"]="sqlite"
    ) -> None:
        self._table_types: Dict[
            Literal["mysql", "postgres", "sqlite"],
            Callable[
                [str],
                Union[
                    JobsMySQLTable,
                    JobsPostgresTable,
                    JobsSQLiteTable
                ]
            ]
        ] = {
            'mysql': lambda table_name: JobsMySQLTable(table_name),
            'postgres': lambda table_name: JobsPostgresTable(table_name),
            'sqlite': lambda table_name: JobsSQLiteTable(table_name)
        }

        self.selected: Union[
            JobsMySQLTable,
            JobsPostgresTable,
            JobsSQLiteTable
        ] = self._table_types.get(
            database_type,
            JobsMySQLTable
        )(users_table_name)

    def select(
        self, 
        filters: Optional[Dict[str, Any]]={}
    ) -> Select:

        select_clause: Select = self.selected.table.select()

        if filters:
            for field_name, value in filters.items():
                select_clause = select_clause.where(
                    self.selected.columns.get(field_name) == self.selected.types_map.get(
                        field_name
                    )(value)
                )

        return select_clause
    
    def insert(
        self,
        jobs: List[M]
    ) -> List[Insert]:
        return [
            self.selected.table.insert().values({
                name: self.selected.types_map.get(
                    name
                )(value) for name, value in job.dict().items()
            }) for job in jobs
        ]
    
    def update(
        self,
        jobs: List[M],
        filters: Optional[Dict[str, Any]]={}
    ) -> List[Update]:
        
        updates: List[Update] = []

        for job in jobs:

            update_clause: Update = self.selected.table.update()

            for field_name, value in filters.items():
                update_clause = update_clause.where(
                    self.selected.columns.get(field_name) == self.selected.types_map.get(
                        field_name
                    )(value)
                )

            update_clause = update_clause.values({
                name: self.selected.types_map.get(
                    name
                )(value) for name, value in job.dict(  
                    exclude_none=True,
                    exclude_unset=True
                ).items()
            })

            updates.append(update_clause)

        return updates
    
    def delete(
        self,
        filters: Dict[str, Any]
    ) -> List[Delete]:
        
        delete_clause: Delete = self.selected.table.delete()

        if filters:
            for field_name, value in filters.items():
                delete_clause = delete_clause.where(
                    self.selected.columns.get(field_name) == self.selected.types_map.get(
                        field_name
                    )(value)
                )

        return delete_clause
        

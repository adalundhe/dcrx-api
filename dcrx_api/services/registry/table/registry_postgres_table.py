import sqlalchemy
import uuid
from sqlalchemy.dialects.postgresql import UUID
from dcrx_api.database.table_types import TableTypes


class RegistryPostgresTable:

    def __init__(
        self, 
        jobs_table_name: str
    ) -> None:
        self.table = sqlalchemy.Table(
            jobs_table_name,
            sqlalchemy.MetaData(),
            sqlalchemy.Column(
                'id', 
                UUID(as_uuid=True),
                primary_key=True,
                default=uuid.uuid4
            ),
            sqlalchemy.Column(
                'registry_name',
                sqlalchemy.TEXT,
                unique=True
            ),
            sqlalchemy.Column(
                'registry_uri',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'registry_user',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'registry_password',
                sqlalchemy.TEXT
            )
        )

        self.columns = {
            'id': self.table.c.id,
            'registry_name': self.table.c.registry_name,
            'registry_uri': self.table.c.registry_uri,
            'registry_user': self.table.c.registry_user,
            'registry_password': self.table.c.registry_password
        }

        self.types_map = {
            'id': lambda value: str(value),
            'registry_name': lambda value: str(value),
            'registry_uri': lambda value: str(value),
            'registry_user': lambda value: str(value),
            'registry_password': lambda value: str(value)
        }

        self.table_type = TableTypes.POSTGRES


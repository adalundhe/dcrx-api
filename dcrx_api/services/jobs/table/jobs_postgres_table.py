import sqlalchemy
import uuid
from sqlalchemy.dialects.postgresql import UUID
from dcrx_api.database.table_types import TableTypes


class JobsPostgresTable:

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
                'image_registry', 
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'name',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'image',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'tag',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'status',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'context',
                sqlalchemy.TEXT
            ),
            sqlalchemy.Column(
                'size',
                sqlalchemy.BIGINT
            )
        )

        self.columns = {
            'id': self.table.c.id,
            'image_registry': self.table.c.image_registry,
            'name': self.table.c.name,
            'image': self.table.c.image,
            'tag': self.table.c.tag,
            'status': self.table.c.status,
            'context': self.table.c.context,
            'size': self.table.c.size
        }

        self.types_map = {
            'id': lambda value: uuid.UUID(value),
            'image_registry': lambda value: str(value),
            'name': lambda value: str(value),
            'image': lambda value: str(value),
            'tag': lambda value: str(value),
            'status': lambda value: str(value),
            'context': lambda value: str(value),
            'size': lambda value: int(value)
        }

        self.table_type = TableTypes.POSTGRES


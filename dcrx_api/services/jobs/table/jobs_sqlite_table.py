import sqlalchemy
import uuid
from dcrx_api.database.table_types import TableTypes


class JobsSQLiteTable:

    def __init__(
        self, 
        jobs_table_name: str
    ) -> None:
        self.table = sqlalchemy.Table(
            jobs_table_name,
            sqlalchemy.MetaData(),
            sqlalchemy.Column(
                'id', 
                sqlalchemy.BLOB,
                primary_key=True,
                default=uuid.uuid4
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
            )
        )

        self.columns = {
            'id': self.table.c.id,
            'name': self.table.c.name,
            'image': self.table.c.image,
            'tag': self.table.c.tag,
            'status': self.table.c.status,
            'context': self.table.c.context,
        }

        self.types_map = {
            'id': lambda value: str(value).encode(),
            'name': lambda value: str(value),
            'image': lambda value: str(value),
            'tag': lambda value: str(value),
            'status': lambda value: str(value),
            'context': lambda value: str(value)
        }

        self.table_type = TableTypes.MYSQL


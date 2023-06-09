import uuid
import asyncio
import click
from dcrx_api.env import load_env, Env
from dcrx_api.auth.auth_context import AuthContext
from dcrx_api.users.users_connection import UsersConnection, ConnectionConfig
from dcrx_api.users.models import DBUser, NewUser
from typing import Dict, Any



async def create_user(
    user: Dict[str, Any],
    env: Env,
):
    
    connection = UsersConnection(
        ConnectionConfig(
            database_username=env.DCRX_API_DATABASE_USER,
            database_password=env.DCRX_API_DATABASE_PASSWORD,
            database_type=env.DCRX_API_DATABASE_TYPE,
            database_uri=env.DCRX_API_DATABASE_URI,
            database_name=env.DCRX_API_DATABASE_NAME
        )
    )

    auth = AuthContext(env)
    await auth.connect()

    new_user = NewUser(
        username=user.get('username'),
        first_name=user.get('first_name'),
        last_name=user.get('last_name'),
        email=user.get('email'),
        disabled=False,
        password=user.get('password')

    )

    hashed_password = await auth.encrypt(new_user.password)

    user = DBUser(
        id=uuid.uuid4(),
        username=new_user.username,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        email=new_user.email,
        disabled=new_user.disabled,
        hashed_password=hashed_password
    )

    await connection.connect()
    await connection.create_table()

    users = await connection.select()

    if len(users) < 1:
        await connection.create([
            user
        ])
    
    await auth.close()
    await connection.close()


@click.group(help='Commands to migrate or initialize the database.')
def database():
    pass


@database.command(help='Initalize the database with the provided administrator.')
@click.option(
    '--username',
    help='Usename for initial admin user.'
)
@click.option(
    '--first-name',
    help='First name of initial admin user.'
)
@click.option(
    '--last-name',
    help='Last name of initial admin user.'
)
@click.option(
    '--email',
    help='Email name of initial admin user.'
)
@click.option(
    '--password',
    help='Password of initial admin user.'
)
def initialize(
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    password: str
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    env = load_env(Env.types_map())

    loop.run_until_complete(
        create_user({
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password
        }, env)
    )


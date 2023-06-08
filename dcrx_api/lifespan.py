from contextlib import asynccontextmanager
from fastapi import FastAPI
from dcrx_api.jobs.job_queue import JobQueue
from dcrx_api.jobs.service import queues, job_context
from dcrx_api.auth.auth_context import AuthContext, active_auth_contexts
from dcrx_api.users.service import users_context
from dcrx_api.users.users_connection import UsersConnection, ConnectionConfig
from .env import load_env, Env


@asynccontextmanager
async def lifespan(router: FastAPI):

    env = load_env(Env.types_map())
    queues['images'] = JobQueue(env)
    job_context['env'] = env
    users_context['env'] = env
    users_context['connection'] = UsersConnection(
        ConnectionConfig(
            database_username=env.DCRX_API_DATABASE_USER,
            database_password=env.DCRX_API_DATABASE_PASSWORD,
            database_type=env.DCRX_API_DATABASE_TYPE,
            database_uri=env.DCRX_API_DATABASE_URI,
            database_name=env.DCRX_API_DATABASE_NAME
        )
    )


    active_auth_contexts['session'] = AuthContext(env)

    await users_context['connection'].connect()
    await active_auth_contexts['session'].connect()
    await users_context['connection'].create_table()

    yield

    await queues['images'].close()
    await active_auth_contexts['session'].close()
    await users_context['connection'].close()
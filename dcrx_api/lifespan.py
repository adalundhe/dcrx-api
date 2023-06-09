from contextlib import asynccontextmanager
from fastapi import FastAPI
from dcrx_api.services.auth.context import (
    AuthorizationSessionManager,
    AuthServiceContext
)
from dcrx_api.services.jobs.context import (
    JobQueue,
    JobsConnection,
    JobServiceContext
)
from dcrx_api.services.users.context import (
    UsersConnection,
    UsersServiceContext
)
from dcrx_api.context.manager import context
from .env import load_env, Env


@asynccontextmanager
async def lifespan(app: FastAPI):

    env = load_env(Env.types_map())

    await context.initialize([
        AuthServiceContext(
            env=env,
            manager=AuthorizationSessionManager(env)
        ),
        JobServiceContext(
            env=env,
            queue=JobQueue(env),
            connection=JobsConnection(env)
        ),
        UsersServiceContext(
            env=env,
            connection=UsersConnection(env)
        )
    ])

    yield

    await context.close()
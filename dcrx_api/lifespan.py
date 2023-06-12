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
from dcrx_api.services.monitoring.context import (
    CPUMonitor,
    DockerMemoryMonitor,
    MemoryMonitor,
    MonitoringServiceContext
)
from dcrx_api.services.registry.context import (
    RegistryConnection,
    RegistryServiceContext
)

from dcrx_api.context.manager import context
from .env import load_env, Env


@asynccontextmanager
async def lifespan(app: FastAPI):

    env = load_env(Env.types_map())

    auth_service_context = AuthServiceContext(
        env=env,
        manager=AuthorizationSessionManager(env)
    )

    job_service_context = JobServiceContext(
        env=env,
        queue=JobQueue(env),
        connection=JobsConnection(env)
    )

    monitoring_service_context = MonitoringServiceContext(
        env=env,
        monitor_name='dcrx.main',
        cpu=CPUMonitor(),
        docker_memory=DockerMemoryMonitor(
            env,
            job_service_context.queue
        ),
        memory=MemoryMonitor()
    )

    registry_service_context = RegistryServiceContext(
        env=env,
        connection=RegistryConnection(env)
    )

    users_service_context = UsersServiceContext(
        env=env,
        connection=UsersConnection(env)
    )

    await context.initialize([
        auth_service_context,
        job_service_context,
        monitoring_service_context,
        registry_service_context,
        users_service_context
    ])

    yield

    await context.close()
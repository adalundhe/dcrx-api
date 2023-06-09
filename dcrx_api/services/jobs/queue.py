import asyncio
import uuid
from dcrx.image import Image
from dcrx_api.env import Env
from .models import BuildOptions
from .models import Registry
from typing import Optional, Dict, Union
from .job import Job
from .connection import JobsConnection
from .status import JobStatus
from .models import (
    JobMetadata,
    JobNotFoundException
)


class JobQueue:

    def __init__(self, env: Env) -> None:

        self.pool_size = env.DCRX_API_WORKERS
        self.push_timeout_minutes = env.DCRX_API_PUSH_TIMEOUT_MINUTES

        self.registry_uri = env.DOCKER_REGISTRY_URI
        self.registry_username = env.DOCKER_REGISTRY_USERNAME
        self.registry_password = env.DOCKER_REGISTRY_PASSWORD

        self._jobs: Dict[uuid.UUID, Job] = {}
        self._active: Dict[uuid.UUID, asyncio.Task] = {}

    def submit(
        self,
        connection: JobsConnection,
        image: Image, 
        build_options: Optional[BuildOptions]=None
    ) -> JobMetadata:

        job = Job(
            connection,
            image,
            Registry(
                registry_uri=self.registry_uri,
                registry_user=self.registry_username,
                registry_password=self.registry_password
                
            ),
            build_options=build_options,
            pool_size=self.pool_size
        )

        self._jobs[job.job_id] = job

        self._active[job.job_id] = asyncio.create_task(
            job.run(self.push_timeout_minutes)
        )

        return job.metadata

    def get(self, job_id: uuid.UUID) -> Union[JobMetadata, JobNotFoundException]:
        job = self._jobs.get(job_id)
        if job is None:
            return JobNotFoundException(
                job_id=job_id,
                message=f'Job - {job_id} - not found.'
            )

        return job.metadata
    
    def cancel(self, job_id: uuid.UUID) -> Union[JobMetadata, JobNotFoundException]:
        job = self._active.get(job_id)
        if job is None or job.done():
            return JobNotFoundException(
                job_id=job_id,
                message=f'Job - {job_id} - not found or is not active.'
            )
        
        job.cancel()

        cancelled_job = self._jobs.get(job_id)

        self._jobs[job_id].close(
            cancelled=True
        )

        return cancelled_job.metadata
    
    async def close(self):
        for job in self._active.values():
            if not job.done():
                job.cancel()

        for job in self._jobs.values():
            await job.close()
            
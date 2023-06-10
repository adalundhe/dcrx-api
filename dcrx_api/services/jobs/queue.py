import asyncio
import uuid
import time
from dcrx.image import Image
from dcrx_api.env import Env
from docker.models.images import Image as DockerImage
from .models import BuildOptions
from .models import Registry
from typing import (
    Optional, 
    Dict, 
    Union,
    List
)
from .job import Job
from .connection import JobsConnection
from .models import (
    JobMetadata,
    JobNotFoundException
)
from .time_parser import TimeParser


class JobQueue:

    def __init__(self, env: Env) -> None:

        self.pool_size = env.DCRX_API_JOB_WORKERS

        self.registry_uri = env.DOCKER_REGISTRY_URI
        self.registry_username = env.DOCKER_REGISTRY_USERNAME
        self.registry_password = env.DOCKER_REGISTRY_PASSWORD

        self._jobs: Dict[uuid.UUID, Job] = {}
        self._active: Dict[uuid.UUID, asyncio.Task] = {}
        self.pool_guard = asyncio.Semaphore(
            value=env.DCRX_API_JOB_POOL_SIZE
        )

        self._cleanup_task: Union[asyncio.Task, None] = None
        self._job_max_age = TimeParser(env.DCRX_API_JOB_MAX_AGE).time
        self._job_prune_interval = TimeParser(env.DCRX_API_JOB_PRUNE_INTERVAL).time
        self._run_cleanup = True
        self.active_images: List[DockerImage] = []

    async def get_active_images(self) -> List[DockerImage]:

        active_statuses = [
            'AUTHORIZING',
            'CREATED',
            'GENERATING',
            'PUSHING'
        ]

        active_images: List[Job] = []

        for active in self._jobs.values():
            if active.metadata.status in active_statuses:
                active_images.append(active)

        images: List[DockerImage] = []

        docker_images = await asyncio.gather(*[
            asyncio.create_task(
                active.list()
            ) for active in active_images
        ])

        for image_set in docker_images:
            images.extend(image_set)

        return images

    async def start(self):
        self._cleanup_task = asyncio.create_task(
            self._monitor_jobs()
        )

    async def _monitor_jobs(self):
        while self._run_cleanup:

            self.active_images = await self.get_active_images()

            queue_jobs = dict(self._jobs)
            
            for job_id, job in queue_jobs.items():
                
                job_elapsed = time.monotonic() - job.job_start_time
                job_is_pruneable = job.metadata.status in ['DONE', 'CANCELLED', 'FAILED']

                if job_is_pruneable and job_elapsed > self._job_max_age:
                    del self._jobs[job_id]
            
            await asyncio.sleep(self._job_prune_interval)

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
            job.run()
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

        self._run_cleanup = False
        await self._cleanup_task

        for job in self._active.values():
            if not job.done():
                job.cancel()

        for job in self._jobs.values():
            await job.close()
            
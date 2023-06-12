import asyncio
import docker
import functools
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dcrx_api.env import Env
from dcrx_api.env.time_parser import TimeParser
from docker.models.images import Image as DockerImage
from typing import (
    Dict, 
    Union,
    List
)
from .job import Job
from .models import (
    JobMetadata,
    JobNotFoundException
)
from .status import JobStatus


class JobQueue:

    def __init__(self, env: Env) -> None:

        self.pool_size = env.DCRX_API_JOB_WORKERS

        self._jobs: Dict[uuid.UUID, Job] = {}
        self._active: Dict[uuid.UUID, asyncio.Task] = {}
        self.pool_guard = asyncio.Semaphore(
            value=env.DCRX_API_JOB_POOL_SIZE
        )
        self._executor = ThreadPoolExecutor(max_workers=env.DCRX_API_JOB_WORKERS)

        self._cleanup_task: Union[asyncio.Task, None] = None
        self._job_max_age = TimeParser(env.DCRX_API_JOB_MAX_AGE).time
        self._job_prune_interval = TimeParser(env.DCRX_API_JOB_PRUNE_INTERVAL).time
        self._run_cleanup = True
        self.active_images: List[DockerImage] = []
        self.cancelling: List[asyncio.Task] = []
        self.client = docker.DockerClient(
            max_pool_size=env.DCRX_API_JOB_WORKERS
        )
        self.completed: List[str] = []
        self.loop = asyncio.get_event_loop()

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

            await self.loop.run_in_executor(
                self._executor,
                functools.partial(
                    subprocess.run,
                    [
                        "docker",
                        "system",
                        "prune",
                        "-f"
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            )

            self.active_images = await self.get_active_images()

            queue_jobs = dict(self._jobs)
            
            for job_id, job in queue_jobs.items():
                
                job_elapsed = time.monotonic() - job.job_start_time
                job_is_pruneable = job.metadata.status in ['DONE', 'CANCELLED', 'FAILED']

                if job.metadata.status == 'CANCELLED':
                    self.cancelling.append(
                        asyncio.create_task(
                            self._cancel_task(job)
                        )
                    )

                if job_is_pruneable and job_elapsed > self._job_max_age:

                    images = await self.loop.run_in_executor(
                        self._executor,
                        self.client.images.list,
                        job.image.name
                    )

                    if len(images) > 0:
                        await self.loop.run_in_executor(
                            self._executor,
                            self.client.images.remove,
                            job.image.name
                        )

                    del self._jobs[job_id]

            
            cancelling_tasks = list(self.cancelling)
            for cancel_task in cancelling_tasks:
                if cancel_task.done():
                    self.cancelling.remove(cancel_task)
            
            await asyncio.sleep(self._job_prune_interval)

    async def _cancel_task(self, job: Job):

        job.client_closed = True

        await job.clear()
        await job.close()

    def submit(self, job: Job) -> JobMetadata:

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
    
    def cancel(self, job_id: uuid.UUID) -> Union[Job, JobNotFoundException]:

        active_task = self._active.get(job_id)
        if active_task and active_task.done() is False:
            active_task.cancel()

        cancellable_states = [
            'CREATED',
            'AUTHORIZING', 
            'BUILDING',
            'GENERATING',
            'PUSHING'
        ]


        cancelled_job = self._jobs.get(job_id)

        if cancelled_job is None:
            return JobNotFoundException(
                job_id=job_id,
                message=f'Job - {job_id} - not found or is not active.'
            )

        job_is_cancellable = cancelled_job.metadata.status in cancellable_states

        if job_is_cancellable is False:
            return JobNotFoundException(
                job_id=job_id,
                message=f'Job - {job_id} - not found or is not active.'
            )
        
        cancelled_job.metadata = JobMetadata(
            id=cancelled_job.job_id,
            image_registry=cancelled_job.registry.registry_uri,
            name=cancelled_job.job_name,
            image=cancelled_job.image.name,
            tag=cancelled_job.image.tag,
            status=JobStatus.CANCELLED.value,
            context=f'Job {cancelled_job.job_id} cancelled.',
            size=cancelled_job.metadata.size
        )
        
        self._jobs[job_id] = cancelled_job

        return cancelled_job
    
    async def close(self):

        self._run_cleanup = False
        await self._cleanup_task

        await self.loop.run_in_executor(
            self._executor,
            self.client.close
        )

        for job in self._active.values():
            if not job.done():
                job.cancel()

        for job in self._jobs.values():
            if job.client_closed is False:
                await job.close()

        self._executor.shutdown(cancel_futures=True)

            
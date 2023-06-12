import asyncio
import docker
import functools
import psutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from docker.errors import (
    ImageNotFound,
    APIError
)
from docker.models.images import Image as DockerImage
from dcrx.image import Image, Label
from dcrx.memory_file import MemoryFile
from dcrx_api.env.time_parser import TimeParser
from dcrx_api.services.registry.models import Registry
from .models import (
    BuildOptions,
    ImageStats,
    JobMetadata,
    JobStepResult
)
from typing import (
    Union, 
    Optional, 
    Dict, 
    Any,
    List
)
from .status import JobStatus
from .connection import JobsConnection


class Job:

    def __init__(
        self, 
        connection: JobsConnection,
        image: Image, 
        registry: Registry,
        build_options: Optional[BuildOptions]=None,
        pool_size: int=psutil.cpu_count(),
        timeout: str='10m',
        wait_timeout: str='10m'
    ) -> None:

        self.job_id = uuid.uuid4()
        self.job_name = image.full_name

        self.image = image
        self.registry = registry
        self.build_options = build_options

        self.client = docker.DockerClient(
            max_pool_size=pool_size,
        )

        self.context: Union[MemoryFile, None] = None
        self._executor = ThreadPoolExecutor(max_workers=pool_size)
        self.loop = asyncio.get_event_loop()
        self.error: Union[Exception, None] = None
        self.connection = connection

        self.metadata = JobMetadata(
            id=self.job_id,
            image_registry=self.registry.registry_uri,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.CREATED.value,
            context=f"Job {self.job_id} created."
        )

        dcrx_api_label = Label(
            name='dcrx.api.id',
            value=str(self.job_id)
        )

        self.image.layers.insert(1, dcrx_api_label)
        self.job_pool_size = pool_size
        self.job_image_label = f'{dcrx_api_label.name}={dcrx_api_label.value}'
        
        self.job_start_time = time.monotonic()
        self.timeout = TimeParser(timeout).time
        self.pending_timeout = TimeParser(wait_timeout).time

        self.image_stats = ImageStats()
        self.shutdown = False
        self.waiter: Union[asyncio.Future, None]=None

    async def list(self) -> List[DockerImage]:
        return await self.loop.run_in_executor(
            self._executor,
            functools.partial(
                self.client.images.list,
                self.image.name
            )
        )
    
    async def run(self):

        if self.waiter:
            self.metadata = JobMetadata(
                id=self.job_id,
                image_registry=self.registry.registry_uri,
                name=self.job_name,
                image=self.image.name,
                tag=self.image.tag,
                status=JobStatus.PENDING.value,
                context=f'Job {self.job_id} pending'
            )

            await self.connection.update([
                self.metadata
            ], filters={
                'id': self.job_id
            })

            try:
                await asyncio.wait_for(
                    self.waiter,
                    timeout=self.pending_timeout
                )

            except (asyncio.CancelledError, asyncio.TimeoutError,):
                await self.cancel()
                return 

        try:
            await asyncio.wait_for(
                asyncio.create_task(
                    self._run(),
                ),
                timeout=self.timeout
            )
        
        except (asyncio.CancelledError, asyncio.TimeoutError,):
            await self.cancel()


    async def _run(self) -> JobStepResult:

        response = await self.connection.create([
            self.metadata
        ])

        if response.error:
            self.error = response.error
            return JobStepResult(
                message='Failed to connect to database',
                error=self.error
            )
        
        job_step_result = JobStepResult(
            message='Job successfully initialized'
        )

        try:
            job_step_result = await self.login_to_registry()
            job_step_result = await self.assemble_context()
            job_step_result = await self.build_image()
            job_step_result = await self.push_image()

        except Exception as job_exception:
            self.error = job_exception
            job_step_result = JobStepResult(
                message='Job failed',
                error=str(job_exception)
            )

        return job_step_result
    
    async def cancel(self):
        self.error = Exception(f'Job {self.job_id} timed out')

        self.metadata = JobMetadata(
            id=self.job_id,
            image_registry=self.registry.registry_uri,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.FAILED.value,
            context=f'Job timed out.'
        )

        await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

    async def login_to_registry(self) -> JobStepResult:

        self.metadata = JobMetadata(
            id=self.job_id,
            image_registry=self.registry.registry_uri,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.AUTHORIZING.value,
            context=f'Job {self.job_id} authorizing to registry {self.registry.registry_uri}'
        )

        response = await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        if response.error:
            self.error = response.error
            return JobStepResult(
                message='Job metadata update failed',
                error=response.error
            )

        await self.loop.run_in_executor(
            self._executor,
            functools.partial(
                self.client.api.login,
                self.registry.registry_user,
                password=self.registry.registry_password,
                registry=self.registry.registry_uri,
                reauth=True
            )
        )

        return JobStepResult(
            message='Registry login succeeded'
        )

    async def assemble_context(self) -> JobStepResult:

        self.metadata = JobMetadata(
            id=self.job_id,
            image_registry=self.registry.registry_uri,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.GENERATING.value,
            context=f'Job {self.job_id} generating image {self.image.full_name}'
        )

        response = await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        if response.error:
            self.error = response.error
            return JobStepResult(
                message='Job metadata update failed',
                error=response.error
            )

        self.context = await self.loop.run_in_executor(
            self._executor,
            self.image.to_context
        )

        return JobStepResult(
            message='DCRX image successfully assembled'
        )

    async def build_image(self) -> JobStepResult:

        self.metadata = JobMetadata(
            id=self.job_id,
            image_registry=self.registry.registry_uri,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.BUILDING.value,
            context=f'Job {self.job_id} building image {self.image.full_name}'
        )

        response = await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        if response.error:
            self.error = response.error
            return JobStepResult(
                message='Job metadata update failed',
                error=response.error
            )

        build_options: Dict[str, Any] = {}

        if self.build_options:
            build_options = self.build_options.dict()

        image_result = await self.loop.run_in_executor(
            self._executor,
            functools.partial(
                self.client.images.build,
                dockerfile=self.image.filename,
                fileobj=self.context,
                tag=self.image.full_name,
                custom_context=True,
                forcerm=True,
                **build_options
            )   
        )

        image, _ = image_result 
        self.image_stats = ImageStats(
            size=int(image.attrs.get('Size', 0)/10**6)
        )

        return JobStepResult(
            message='Docker image successfully built'
        )
        
    async def push_image(self) -> JobStepResult:

        self.metadata = JobMetadata(
            id=self.job_id,
            image_registry=self.registry.registry_uri,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.PUSHING.value,
            context=f'Job {self.job_id} pushing image {self.image.full_name} to registry {self.registry.registry_uri}',
            size=self.image_stats.size
        )

        response = await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        if response.error:
            self.error = response.error
            return JobStepResult(
                message='Job metadata update failed',
                error=response.error
            )

        await self.loop.run_in_executor(
            self._executor,
            functools.partial(        
                self.client.images.push,
                self.image.name,
                tag=self.image.tag
            )
        )

        return JobStepResult(
            message='Docker image successfully pushed'
        )


    async def close(self):

        self.shutdown = True
        if self._executor and self._executor._shutdown:
            self._executor = None

        await self._clear()

        if self.error is None:
            status = JobStatus.DONE
            context = f'Job {self.job_id} complete'

        elif self.metadata.status == JobStatus.CANCELLED.value:
            status = JobStatus.CANCELLED
            context = f'Job {self.job_id} cancelled'

        else:
            status = JobStatus.FAILED
            context = str(self.error)

        self.metadata = JobMetadata(
            id=self.job_id,
            image_registry=self.registry.registry_uri,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=status.value,
            context=context,
            size=self.image_stats.size
        )
        

        await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        await self.loop.run_in_executor(
            None,
            self.client.close
        )

        if self.context:
            await self.loop.run_in_executor(
                self._executor,
                self.context.close
            )

        if self._executor:
            self._executor.shutdown(cancel_futures=True)
        
    async def _clear(self):

        try:
            await self.loop.run_in_executor(
                self._executor,
                self.client.api.prune_builds
            )

            await self.loop.run_in_executor(
                self._executor,
                functools.partial(      
                    self.client.api.prune_images
                )
            )
        
        except APIError:
            pass

        for layer in self.image.layers:
            if layer.layer_type == 'stage':

                try:
                    await self.loop.run_in_executor(
                        self._executor,
                        functools.partial(
                            self.client.images.remove,
                            f'{layer.base}:{layer.tag}'
                        )
                    )
                
                except ImageNotFound:
                    pass

        try:
            await self.loop.run_in_executor(
                self._executor,
                functools.partial(
                    self.client.images.remove,
                    self.image.full_name
                )
            )

        except ImageNotFound:
            pass

        await self.loop.run_in_executor(
            self._executor,
            self.image.clear
        )
    
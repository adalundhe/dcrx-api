import asyncio
import docker
import functools
import psutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dcrx.image import Image, Label
from dcrx.memory_file import MemoryFile
from .models import (
    BuildOptions,
    JobMetadata,
    Registry
)
from typing import (
    Union, 
    Optional, 
    Dict, 
    Any
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
        pool_size: int=psutil.cpu_count()
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
        self.job_image_label = f'{dcrx_api_label.name}={dcrx_api_label.value}'
    
        self.push_timeout_minutes: Union[int, None] = None

    async def run(
        self,
        timeout: int
    ):

        self.push_timeout_minutes = timeout
        
        await self.connection.create([
            self.metadata
        ])

        try:
            await self.login_to_registry()
            await self.assemble_context()
            await self.build_image()
            await self.push_image()

        except Exception as job_exception:
            self.error = job_exception

        await self.clear()
        await self.close()

    async def login_to_registry(self):

        self.metadata = JobMetadata(
            id=self.job_id,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.AUTHORIZING.value,
            context=f'Job {self.job_id} authorizing to registry {self.registry.registry_uri}'
        )

        await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

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

    async def assemble_context(self):

        self.metadata = JobMetadata(
            id=self.job_id,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.GENERATING.value,
            context=f'Job {self.job_id} generating image {self.image.full_name}'
        )

        await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        self.context = await self.loop.run_in_executor(
            self._executor,
            self.image.to_context
        )


    async def build_image(self):

        self.metadata = JobMetadata(
            id=self.job_id,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.BUILDING.value,
            context=f'Job {self.job_id} building image {self.image.full_name}'
        )

        await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        build_options: Dict[str, Any] = {}

        if self.build_options:
            build_options = self.build_options.dict()

        await self.loop.run_in_executor(
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


    async def push_image(self):

        self.metadata = JobMetadata(
            id=self.job_id,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=JobStatus.PUSHING.value,
            context=f'Job {self.job_id} pushing image {self.image.full_name} to registry {self.registry.registry_uri}'
        )

        await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        await self.loop.run_in_executor(
            self._executor,
            functools.partial(        
                self.client.images.push,
                self.image.name,
                tag=self.image.tag
            )
        )

    async def clear(self):

        for layer in self.image.layers:
            if layer.layer_type == 'stage':
                await self.loop.run_in_executor(
                    self._executor,
                    functools.partial(
                        self.client.images.remove,
                        f'{layer.base}:{layer.tag}'
                    )
                )

        await self.loop.run_in_executor(
            self._executor,
            functools.partial(
                self.client.images.remove,
                self.image.full_name
            )
        )

        await self.loop.run_in_executor(
            self._executor,
            self.image.clear
        )


    async def close(
        self,
        cancelled: bool=False    
    ):

        if self.error is None:
            status = JobStatus.DONE
            context = f'Job {self.job_id} complete'

        elif cancelled:
            status = JobStatus.CANCELLED
            context = f'Job {self.job_id} cancelled'

        else:
            status = JobStatus.FAILED
            context = str(self.error)

        self.metadata = JobMetadata(
            id=self.job_id,
            name=self.job_name,
            image=self.image.name,
            tag=self.image.tag,
            status=status.value,
            context=context
        )
        

        await self.connection.update([
            self.metadata
        ], filters={
            'id': self.job_id
        })

        self._executor.shutdown(cancel_futures=True)
        self.client.close()
        self.context.close()
        



    
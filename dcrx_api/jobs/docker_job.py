import asyncio
import docker
import functools
import traceback
import os
import psutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from dcrx.image import Image
from dcrx.memory_file import MemoryFile
from .models import BuildOptions
from .models import Registry
from typing import (
    Union, 
    Optional, 
    Dict, 
    Any
)
from .job_status import JobStatus


class DockerJob:

    def __init__(
        self, 
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
        self.status = JobStatus.CREATED
        self.error: Union[Exception, None] = None

    async def run(self):

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

        self.status = JobStatus.AUTHORIZING

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

        self.status = JobStatus.GENERATING

        self.context = await self.loop.run_in_executor(
            self._executor,
            self.image.to_context
        )


    async def build_image(self):

        self.status = JobStatus.BUILDING

        build_options: Dict[str, Any] = {}

        if self.build_options:
            build_options = self.build_options.dict()

        await self.loop.run_in_executor(
            self._executor,
            functools.partial(
                self.client.api.build,
                dockerfile=self.image.filename,
                fileobj=self.context,
                tag=self.image.full_name,
                custom_context=True,
                **build_options
            )   
        )

    async def push_image(self):

        self.status = JobStatus.PUSHING

        await self.loop.run_in_executor(
            self._executor,
            functools.partial(
                self.client.api.push,
                self.image.name,
                tag=self.image.tag
            )
        )

    async def clear(self):
        await self.loop.run_in_executor(
            self._executor,
            self.image.clear
        )
            

    async def close(self):

        self._executor.shutdown(cancel_futures=True)
        self.client.close()
        self.context.close()

        if self.error is None:
            self.status = JobStatus.DONE

        else:
            self.status = JobStatus.FAILED
        



    
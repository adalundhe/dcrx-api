
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .job_queue import JobQueue
from .images import queues


@asynccontextmanager
async def lifespan(router: FastAPI):
    queues['images'] = JobQueue()
    yield
    await queues['images'].close()
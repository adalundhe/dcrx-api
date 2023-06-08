import os
import uuid
import psutil
from dcrx import Image
from .job_queue import JobQueue
from fastapi import APIRouter, HTTPException
from typing import Dict
from .models import (
    NewImage,
    JobMetadata,
    JobNotFoundException
)

queues: Dict[str, JobQueue] = {}
pool_size = int(os.getenv("DCRX_API_WORKERS", psutil.cpu_count()))



jobs_router = APIRouter()


@jobs_router.post("/jobs/images/create")
async def start_job(new_image: NewImage) -> JobMetadata:

    job_queue = queues.get('images')

    dcrx_image = Image(
        new_image.name,
        tag=new_image.tag,
        registry=new_image.registry
    )

    for layer in new_image.layers:
        dcrx_image.layers.append(layer)

    return job_queue.submit(
        dcrx_image,
        new_image.registry,
        build_options=new_image.build_options
    )


@jobs_router.get(
    "/jobs/images/{job_id}/get",
    responses={
        404: {
            "model": JobNotFoundException
        }
    }
)
async def get_job(job_id: str) -> JobMetadata:
    job_queue = queues.get('images')
    retrieved_job = job_queue.get(
        uuid.UUID(job_id)
    )

    if isinstance(retrieved_job, JobNotFoundException):
        raise HTTPException(404, detail=retrieved_job.message)
    
    return retrieved_job


@jobs_router.delete(
    "/jobs/images/{job_id}/cancel",
    responses={
        404: {
            "model": JobNotFoundException
        }
    }
)
async def cancel_job(job_id: str) -> JobMetadata:
    job_queue = queues.get('images')
    cancelled_job = job_queue.cancel(
        uuid.UUID(job_id)
    )

    if isinstance(cancelled_job, JobNotFoundException):
        raise HTTPException(404, detail=cancelled_job.message)

    return cancelled_job
    


    
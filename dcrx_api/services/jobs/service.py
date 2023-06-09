import uuid
from dcrx import Image
from dcrx_api.context.manager import context, ContextType
from fastapi import APIRouter, HTTPException
from .models import (
    NewImage,
    JobMetadata,
    JobNotFoundException
)


jobs_router = APIRouter()


@jobs_router.post("/jobs/images/create")
async def start_job(new_image: NewImage) -> JobMetadata:

    job_service_context = context.get(ContextType.JOB_SERVICE)

    dcrx_image = Image(
        new_image.name,
        tag=new_image.tag
    )

    for layer in new_image.layers:
        dcrx_image.layers.append(layer)

    return job_service_context.queue.submit(
        job_service_context.connection,
        dcrx_image,
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

    job_service_context = context.get(ContextType.JOB_SERVICE)

    retrieved_job = job_service_context.queue.get(
        uuid.UUID(job_id)
    )

    if isinstance(retrieved_job, JobNotFoundException):

        retrieved_jobs = await job_service_context.connection.select(
            filters={
                'id': job_id
            }
        )

        if len(retrieved_jobs) < 1:
            raise HTTPException(404, detail=retrieved_job.message)
        
        retrieved_job = retrieved_jobs.pop()
    
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

    job_service_context = context.get(ContextType.JOB_SERVICE)

    cancelled_job = job_service_context.queue.cancel(
        uuid.UUID(job_id)
    )

    if isinstance(cancelled_job, JobNotFoundException):
        raise HTTPException(404, detail=cancelled_job.message)

    return cancelled_job
    


    
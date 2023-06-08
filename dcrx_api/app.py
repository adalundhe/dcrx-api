from fastapi import FastAPI
from dcrx_api.jobs.images import jobs_router
from dcrx_api.jobs.lifespan import lifespan

app = FastAPI(lifespan=lifespan)
app.include_router(jobs_router)


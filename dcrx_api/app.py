from fastapi import FastAPI
from dcrx_api.jobs.service import jobs_router
from dcrx_api.users.service import users_router
from dcrx_api.lifespan import lifespan
from dcrx_api.middleware.auth_middleware import AuthMidlleware

app = FastAPI(lifespan=lifespan)
app.include_router(jobs_router)
app.include_router(users_router)
app.add_middleware(AuthMidlleware)
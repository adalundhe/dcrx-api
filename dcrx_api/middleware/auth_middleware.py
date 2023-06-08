import json
from dcrx_api.auth.auth_context import active_auth_contexts
from dcrx_api.users.service import users_context
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMidlleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        allowed_urls = [
            "/docs",
            "/favicon.ico",
            "/openapi.json",
            "/users/login"
        ]
        
        if request.url.path in allowed_urls:
            response = await call_next(request)
            return response


        token = request.cookies.get('X-Auth-Token')

        auth = active_auth_contexts.get('session')
        connection = users_context.get('connection')

        authorization = await auth.verify_token(
            connection,
            token
        )

        if authorization.error:
            return Response(
                status_code=401,
                content=json.dumps({
                    'detail': authorization.error
                })
            )

        response = await call_next(request)
        return response
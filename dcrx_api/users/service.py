import uuid
import datetime
from dcrx_api.env import Env
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from dcrx_api.auth.auth_context import active_auth_contexts
from dcrx_api.auth.models import AuthenticationFailureException
from typing import (
    Dict,
    Literal, 
    Union
)
from .models import (
    AuthorizedUser,
    DBUser,
    LoginUser,
    NewUser,
    UpdatedUser,
    UserNotFoundException,
    UserTransactionSuccessResponse,
)
from .users_connection import UsersConnection


users_context: Dict[str,Union[Env, UsersConnection]] = {}


users_router = APIRouter()


@users_router.post(
    '/users/login',
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def login_user(user: LoginUser) -> UserTransactionSuccessResponse:
    users_connection = users_context.get('connection')
    auth = active_auth_contexts.get('session')

    authorization = await auth.generate_token(
        users_connection,
        user
    )

    if authorization.error:
        raise HTTPException(401, detail=authorization.error)
    
    success_response = UserTransactionSuccessResponse(
        message='User logged in.'
    )

    response = JSONResponse(
        content=success_response.dict()
    )

    response.set_cookie(
        key='X-Auth-Token',
        value=authorization.token,
        expires=authorization.token_expires
    )


    return response


@users_router.get(
    '/users/{user_id_or_name}/get',
    responses={
        401: {
            "model": AuthenticationFailureException
        },
        404: {
            "model": UserNotFoundException
        }
    }
)
async def get_user(
    user_id_or_name: str, 
    match_by: Literal["id", "username"]="id"
) -> AuthorizedUser:
    users_connection = users_context.get('connection')

    filters = {
        'id': user_id_or_name
    }

    if match_by == 'username':
        filters = {
            'username': user_id_or_name
        }

    users = await users_connection.select(
        filters=filters
    )

    if len(users) < 1:
        raise HTTPException(404, detail=f'User {user_id_or_name} not found.')
    
    user = users.pop()
    
    return AuthorizedUser(
        id=user.id,
        username=user.username
    )


@users_router.post(
    '/users/create',
    status_code=201,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def create_user(user: NewUser) -> UserTransactionSuccessResponse:
    users_connection = users_context.get('connection')
    auth = active_auth_contexts.get('session')

    hashed_password = await auth.encrypt(user.password)

    await users_connection.create([
        DBUser(
            id=uuid.uuid4(),
            hashed_password=hashed_password,
            **user.dict(exclude={"password"})
        )
    ])

    return UserTransactionSuccessResponse(
        message='Created user.'
    )


@users_router.put(
    '/users/update',
    status_code=202,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def update_user(user: UpdatedUser) -> UserTransactionSuccessResponse:
    users_connection = users_context.get('connection')

    await users_connection.create([
        user
    ])

    return UserTransactionSuccessResponse(
        message='Updated user.'
    )


@users_router.delete(
    '/users/{user_id}/delete',
    status_code=200,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def delete_user(user_id: str) -> UserTransactionSuccessResponse:
    users_connection = users_context.get('connection')

    await users_connection.delete(
        filters={
            'id': user_id
        }
    )

    return UserTransactionSuccessResponse(
        message='Deleted user.'
    )
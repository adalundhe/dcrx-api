import uuid
from dcrx_api.services.auth.models import AuthenticationFailureException
from dcrx_api.context.manager import context, ContextType
from dcrx_api.database.models import DatabaseTransactionResult
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Literal
from .models import (
    AuthorizedUser,
    DBUser,
    LoginUser,
    NewUser,
    UpdatedUser,
    UserNotFoundException,
    UserTransactionSuccessResponse,
)

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

    users_service_context = context.get(ContextType.USERS_SERVICE)
    auth_service_context = context.get(ContextType.AUTH_SERVICE)

    authorization = await auth_service_context.manager.generate_token(
        users_service_context.connection,
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
        value=f'Bearer {authorization.token}',
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
        },
        500: {
            "model": DatabaseTransactionResult
        }
    }
)
async def get_user(
    user_id_or_name: str, 
    match_by: Literal["id", "username"]="id"
) -> AuthorizedUser:

    users_service_context = context.get(ContextType.USERS_SERVICE)

    filters = {
        'id': user_id_or_name
    }

    if match_by == 'username':
        filters = {
            'username': user_id_or_name
        }

    response = await users_service_context.connection.select(
        filters=filters
    )

    if response.data is None or len(response.data) < 1:
        raise HTTPException(404, detail=f'User {user_id_or_name} not found.')
    
    elif response.error:
        raise HTTPException(500, detail={
            "message": response.message,
            "error": response.error
        })
    
    user = response.data.pop()
    
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
        },
        500: {
            "model": DatabaseTransactionResult
        }
    }
)
async def create_user(user: NewUser) -> UserTransactionSuccessResponse:

    users_service_context = context.get(ContextType.USERS_SERVICE)
    auth_service_context = context.get(ContextType.AUTH_SERVICE)

    hashed_password = await auth_service_context.manager.encrypt(user.password)

    response = await users_service_context.connection.create([
        DBUser(
            id=uuid.uuid4(),
            hashed_password=hashed_password,
            **user.dict(exclude={"password"})
        )
    ])

    if response.error:
        raise HTTPException(500, detail={
            "message": response.message,
            "error": response.error
        })

    return UserTransactionSuccessResponse(
        message='Created user.'
    )


@users_router.put(
    '/users/update',
    status_code=202,
    responses={
        401: {
            "model": AuthenticationFailureException
        },
        500: {
            "model": DatabaseTransactionResult
        }
    }
)
async def update_user(user: UpdatedUser) -> UserTransactionSuccessResponse:

    users_service_context = context.get(ContextType.USERS_SERVICE)

    response = await users_service_context.connection.update([
        user
    ])

    if response.error:
        raise HTTPException(500, detail={
            "message": response.message,
            "error": response.error
        })

    return UserTransactionSuccessResponse(
        message='Updated user.'
    )


@users_router.delete(
    '/users/{user_id}/delete',
    status_code=200,
    responses={
        401: {
            "model": AuthenticationFailureException
        },
        500: {
            "model": DatabaseTransactionResult
        }
    }
)
async def delete_user(user_id: str) -> UserTransactionSuccessResponse:

    users_service_context = context.get(ContextType.USERS_SERVICE)

    response = await users_service_context.connection.remove(
        filters={
            'id': user_id
        }
    )

    if response.error:
        raise HTTPException(500, detail={
            "message": response.message,
            "error": response.error
        })

    return UserTransactionSuccessResponse(
        message='Deleted user.'
    )
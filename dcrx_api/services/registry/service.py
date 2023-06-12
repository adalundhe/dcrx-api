import uuid
from dcrx_api.services.auth.models import AuthenticationFailureException
from dcrx_api.context.manager import context, ContextType
from fastapi import APIRouter, HTTPException
from typing import Literal
from .context import RegistryServiceContext
from .models import (
    RegistryMetadata,
    RegistryNotFoundException,
    Registry,
    RegistryTransactionSuccessResponse
)

registry_router = APIRouter()


@registry_router.get(
    '/registry/{registry_id_or_name}/get',
    responses={
        401: {
            "model": AuthenticationFailureException
        },
        404: {
            "model": RegistryNotFoundException
        }
    }
)
async def get_registry(
    registry_id_or_name: str, 
    match_by: Literal["id", "registry_uri"]="id"
) -> RegistryTransactionSuccessResponse:

    registry_service_context: RegistryServiceContext = context.get(ContextType.REGISTRY_SERVICE)

    filters = {
        'id': registry_id_or_name
    }

    if match_by == 'registry_uri':
        filters = {
            'registry_uri': registry_id_or_name
        }

    registries = await registry_service_context.connection.select(
        filters=filters
    )

    if len(registries) < 1:
        raise HTTPException(404, detail=f'Registry {registry_id_or_name} not found.')
    
    registry = registries.pop()
    
    return RegistryTransactionSuccessResponse(
        id=registry.id,
        registry_name=registry.registry_name,
    )


@registry_router.post(
    '/registry/create',
    status_code=201,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def create_registry(registry: RegistryMetadata) -> RegistryTransactionSuccessResponse:

    registry_service_context: RegistryServiceContext = context.get(ContextType.REGISTRY_SERVICE)
    auth_service_context = context.get(ContextType.AUTH_SERVICE)

    hashed_password = await auth_service_context.manager.encrypt_fernet(
        registry.registry_password
    )

    new_registry_id = uuid.uuid4()
    await registry_service_context.connection.create([
        Registry(
            id=new_registry_id,
            registry_name=registry.registry_name,
            registry_uri=registry.registry_uri,
            registry_user=registry.registry_user,
            registry_password=hashed_password
        )
    ])

    return RegistryTransactionSuccessResponse(
        id=new_registry_id,
        registry_name=registry.registry_name,
        message='Successfully created'
    )


@registry_router.put(
    '/registry/update',
    status_code=202,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def update_registry(registry: Registry) -> RegistryTransactionSuccessResponse:

    registry_service_context: RegistryServiceContext = context.get(ContextType.REGISTRY_SERVICE)

    await registry_service_context.connection.update([
        registry
    ])

    return RegistryTransactionSuccessResponse(
        id=registry.id,
        registry_name=registry.registry_name,
        message='Successfully updated'
    )


@registry_router.delete(
    '/registry/{registry_id}/delete',
    status_code=200,
    responses={
        401: {
            "model": AuthenticationFailureException
        }
    }
)
async def delete_registry(registry_id: str) -> RegistryTransactionSuccessResponse:

    registry_service_context: RegistryServiceContext = context.get(ContextType.REGISTRY_SERVICE)

    await registry_service_context.connection.remove(
        filters={
            'id': registry_id
        }
    )

    return RegistryTransactionSuccessResponse(
        id=registry_id,
        message='Successfully deleted'
    )
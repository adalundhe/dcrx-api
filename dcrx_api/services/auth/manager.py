import asyncio
import datetime
import functools
from concurrent.futures import ThreadPoolExecutor
from dcrx_api.env import Env
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import (
    Optional,
    Dict,
    Any,
    List,
    Union
)
from dcrx_api.services.users.connection import UsersConnection
from dcrx_api.services.users.models import (
    DBUser,
    LoginUser
)
from .models import (
    AuthResponse,
    AuthClaims,
    GeneratedToken
)


class AuthorizationSessionManager:

    def __init__(self, env: Env) -> None:

        self.pool_size = env.DCRX_API_WORKERS
        self.context = CryptContext(
            schemes=["bcrypt"], 
            deprecated="auto"
        )

        self.scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.secret_key = env.DCRX_API_SECRET_KEY
        self.auth_algorithm = env.DCRX_API_AUTH_ALGORITHM
        self.token_expiration_minutes = env.DCRX_API_TOKEN_EXPIRATION_MINUTES

        self._executor: Union[ThreadPoolExecutor, None] = None
        self._loop: Union[asyncio.AbstractEventLoop, None] = None

    async def connect(self):
        self._loop = asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor(max_workers=self.pool_size)

    async def encrypt(self, password: str):
        return await self._loop.run_in_executor(
            self._executor,
            functools.partial(
                self.context.hash,
                password
            )
        )

    async def authenticate_user(
        self,
        db_connection: UsersConnection,
        username: str, 
        password: str
    ) -> Union[DBUser, None]:
        users: List[DBUser] = await db_connection.select(
            filters={
                'username': username
            }
        )

        if len(users) < 1:
            return AuthResponse(
                error='User authorization failed',
                message='Authentication failed'
            )
        
        user = users.pop()
        
        password_verified = await self._loop.run_in_executor(
            self._executor,
            functools.partial(
                self.context.verify,
                password, 
                user.hashed_password
            )
        )

        if password_verified is False:
            return AuthResponse(
                error='User authorization failed',
                message='Authentication failed'
            )
        
        
        return user
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[datetime.datetime]=None
    ):

        to_encode = data.copy()

        expiration: datetime.datetime = datetime.datetime.utcnow() + expires_delta

        to_encode.update({
            "exp": expiration
        })

        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key, 
            algorithm=self.auth_algorithm
        )

        return GeneratedToken(
            token=encoded_jwt,
            expiration=int(expiration.timestamp()/10**7)
        )
    
    async def generate_token(
        self,
        db_connection: UsersConnection,
        login_user: LoginUser
    ) -> AuthResponse:
        user = await self.authenticate_user(
            db_connection, 
            login_user.username, 
            login_user.password
        )

        if isinstance(user, AuthResponse):
            return user

        access_token_expires = datetime.timedelta(
            minutes=self.token_expiration_minutes
        )
        
        auth_token = self.create_access_token(
            data={
                "sub": user.username
            }, 
            expires_delta=access_token_expires
        )

        return AuthResponse(
            message='Loggin success',
            token=auth_token.token,
            token_expires=auth_token.expiration
        )
    
    async def verify_token(
        self,
        connection: UsersConnection,
        token: Union[str, None]
    ):

        try:

            if token is None:
                return AuthResponse(
                    error='No token provided',
                    message='Authentication failed'
                )

            payload = await self._loop.run_in_executor(
                self._executor,
                functools.partial(
                    jwt.decode,
                    token, 
                    self.secret_key, 
                    algorithms=[self.auth_algorithm]
                )
            )

            username: str = payload.get("sub")
            if username is None:
                return AuthResponse(
                    error='User not found',
                    message='Authentication failed'
                )
            
            token_data = AuthClaims(username=username)

        except JWTError as validation_error:
            return AuthResponse(
                    error=str(validation_error),
                    message='Authentication failed'
                )
        
        users: List[DBUser] = await connection.select(
            filters={
                'username': token_data.username
            }
        )

        if len(users) < 1:
            return AuthResponse(
                error='User not found',
                message='Authentication failed'
            )
        
        return AuthResponse(
            message='OK'
        )
    
    async def close(self):
        self._executor.shutdown(cancel_futures=True)
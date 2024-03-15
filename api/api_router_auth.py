from fastapi import APIRouter, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm

from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from library.security_lib import AuthHandler
from api.schemas_user import LoginResponse


public_router = APIRouter(
    prefix='/api/auth',
    tags=['API', 'Auth']
)


@public_router.post('/login')
async def user_login(
        data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_async_session),
) -> LoginResponse:
    token_pair = await AuthHandler.get_login_token_pairs(data, session)
    return token_pair


@public_router.post('/refresh')
async def refresh_user_token(
        refresh_token=Header(), session: AsyncSession = Depends(get_async_session),
) -> LoginResponse:
    token_pair = await AuthHandler.get_refresh_token(refresh_token, session)
    return token_pair


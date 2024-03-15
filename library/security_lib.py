import uuid
from datetime import timedelta, datetime
import jwt

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_session

from api.schemas_user import LoginResponse
import dao
from models import User
from settings import settings


class PasswordEncrypt:
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    @classmethod
    async def get_password_hash(cls, password: str) -> str:
        return cls.pwd_context.hash(password)

    @classmethod
    async def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return cls.pwd_context.verify(plain_password, hashed_password)


class AuthHandler:
    secret = settings.JWT_SECRET
    algorithm = settings.JWT_ALGORITHM

    @classmethod
    async def get_login_token_pairs(cls, data: OAuth2PasswordRequestForm, session: AsyncSession) -> LoginResponse:
        user = await dao.get_user_by_email(email=data.username, session=session)

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User with this email not found')
        is_valid_password = await PasswordEncrypt.verify_password(data.password, user.hashed_password)
        if not is_valid_password:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Password is incorrect')
        if not user.verified_at:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Your account is not verified')
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are banned. Please contact support')

        token_pairs: LoginResponse = await cls.generate_token_pair(user, session)
        return token_pairs

    @classmethod
    async def generate_token(cls, payload: dict, expiry: timedelta) -> str:
        now = datetime.utcnow()
        time_payload = {'exp': now + expiry, 'iat': now}
        payload.update(time_payload)
        token_ = jwt.encode(payload, cls.secret, cls.algorithm)
        return token_

    @classmethod
    async def decode_token(cls, token: str) -> dict:
        try:
            payload = jwt.decode(token, cls.secret, [cls.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Time is out')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid token')

    @classmethod
    async def decode_token_web(cls, token: str) -> dict:
        try:
            payload = jwt.decode(token, cls.secret, [cls.algorithm])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return {}

    @classmethod
    async def generate_token_pair(cls, user: User, session: AsyncSession) -> LoginResponse:
        access_token_payload = {
            'sub': user.id,
            'email': user.email,
        }
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_TIME_MINUTES)
        access_token = await cls.generate_token(access_token_payload, access_token_expires)

        refresh_token_payload = {
            'sub': user.id,
            'email': user.email,
            'key': str(uuid.uuid4()),
        }
        refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_TIME_MINUTES)
        refresh_token = await cls.generate_token(refresh_token_payload, refresh_token_expires)
        await dao.create_refresh_token(
            user_id=user.id,
            refresh_key=refresh_token_payload['key'],
            expires_at=datetime.utcnow() + refresh_token_expires,
            session=session,
        )
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=access_token_expires.seconds,
        )

    @classmethod
    async def get_refresh_token(cls, refresh_token: str, session: AsyncSession) -> LoginResponse:
        payload = await cls.decode_token(refresh_token)

        refresh_token_key = payload.get('key')
        user_token = await dao.get_refresh_token_by_key(refresh_token_key, session)
        if not user_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid token')
        user_token.expires_at = datetime.utcnow()
        session.add(user_token)
        await session.commit()
        token_pair = await cls.generate_token_pair(user_token.user, session)
        return token_pair


class SecurityHandler:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

    @classmethod
    async def get_current_user(
        cls, token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)
    ):
        payload = await AuthHandler.decode_token(token)
        user = await dao.get_user_by_email(email=payload.get('email'), session=session)
        if user:
            return user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User unknown')

    @classmethod
    async def get_current_user_web(
        cls, request: Request, session: AsyncSession = Depends(get_async_session)
    ):
        token = request.cookies.get('token') or ''
        payload = await AuthHandler.decode_token_web(token)
        user = await dao.get_user_by_email(email=payload.get('email'), session=session)
        return user

    @classmethod
    async def set_cookies_web(cls, user, response):
        if not user:
            return response

        access_token_payload = {
            'sub': user.id,
            'email': user.email,
        }
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_TIME_MINUTES)
        token = await AuthHandler.generate_token(payload=access_token_payload, expiry=access_token_expires)
        response.set_cookie(key='token', value=token, httponly=True)

        return response

    @classmethod
    async def authenticate_user_web(cls, email, password, session: AsyncSession):
        user = await dao.get_user_by_email(email, session)
        is_password_correct = await PasswordEncrypt.verify_password(password, user.hashed_password) if user else False
        return user, is_password_correct

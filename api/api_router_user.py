from fastapi import APIRouter, status, Depends, HTTPException, Request, BackgroundTasks
from api.schemas_user import RegisterUserRequest, BaseFields
from database import get_async_session
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import dao
from library.security_lib import PasswordEncrypt
from library.email_sender import send_email_verification


router = APIRouter(
    prefix='/api/user',
    tags=['Users', 'API']
)


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_user_account(
        request: Request,
        new_user: RegisterUserRequest,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
) -> RegisterUserRequest:

    maybe_user = await dao.get_user_by_email(new_user.email, session)
    if maybe_user:
        raise HTTPException(detail=f'User {maybe_user.name} with email {maybe_user.email} already exists',
                            status_code=status.HTTP_403_FORBIDDEN)

    hashed_password = await PasswordEncrypt.get_password_hash(new_user.password)

    saved_user = await dao.create_user(
        name=new_user.name,
        email=new_user.email,
        hashed_password=hashed_password,
        session=session,
    )
    background_tasks.add_task(
        send_email_verification,
        user_email=saved_user.email,
        user_uuid=saved_user.user_uuid,
        user_name=saved_user.name,
        host=request.base_url,
    )

    return new_user


@router.get("/verify/{user_uuid}")
async def verify_user_account(user_uuid: str, session: AsyncSession = Depends(get_async_session)) -> dict:
    user = await dao.activate_user_account(user_uuid, session)
    return {'user_email': user.email, 'verified': True}

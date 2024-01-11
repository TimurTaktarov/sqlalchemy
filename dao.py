from asyncpg import UniqueViolationError
from sqlalchemy import insert, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from models import User
from database import async_session_maker


async def create_user(
        name: str,
        email: str,
        hashed_password: str,
        session: AsyncSession,
) -> User:
    user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
    )
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(detail=f'User with email {email} probably already exists',
                            status_code=status.HTTP_403_FORBIDDEN)


async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    query = select(User).filter_by(email=email)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_uuid(user_uuid: str, session: AsyncSession) -> User | None:
    query = select(User).filter_by(user_uuid=user_uuid)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def activate_user_account(user_uuid: str, session: AsyncSession) -> User | None:
    user = await get_user_by_uuid(user_uuid, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data for account activation is not correct"
        )
    if user.verified_at:
        return user

    user.verified_at = True
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
# async def fetch_users(skip: int = 0, limit: int = 10) -> list[User]:
#     async with async_session_maker() as session:
#         query = select(User).offset(skip).limit(limit)
#         result = await session.execute(query)
#         print(query)
#         # print(type(result.scalars().all()))
#         print(result.scalars().all()[0].login)
#         # print(result.scalars().all()[0].__dict__)
#         return result.scalars().all()
#
#
# async def get_user_by_id(user_id: int) -> User | None:
#     async with async_session_maker() as session:
#         query = select(User).filter_by(id=user_id)
#         result = await session.execute(query)
#         # print(result.scalar_one_or_none())
#         return result.scalar_one_or_none()
#
#
# async def update_user(user_id: int, values: dict):
#     if not values:
#         return
#     async with async_session_maker() as session:
#         query = update(User).where(User.id == user_id).values(**values)
#         result = await session.execute(query)
#         await session.commit()
#         # print(tuple(result))
#         print(query)
#
#
# async def delete_user(user_id: int):
#     async with async_session_maker() as session:
#         query = delete(User).where(User.id == user_id)
#         await session.execute(query)
#         await session.commit()
#         print(query)

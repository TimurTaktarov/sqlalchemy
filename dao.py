from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload

from models import User, UserRefreshToken, Product, OrderProduct, Order, Comments
from database import async_session_maker

import datetime


async def create_user(
        name: str,
        email: str,
        hashed_password: str,
        session: AsyncSession,
        is_admin: bool = False,
        avatar: str = '',
) -> User:
    user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        is_admin=is_admin,
        avatar=avatar,
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


async def is_first_user(session: AsyncSession) -> bool:
    query = select(User).limit(1)
    user_count = await session.execute(query)
    user_count = user_count.scalar_one_or_none()
    return not bool(user_count)


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


async def fetch_users(skip: int = 0, limit: int = 10) -> list[User]:
    async with async_session_maker() as session:
        query = select(User).offset(skip).limit(limit)
        result = await session.execute(query)

        return result.scalars().all()

# async def get_user_by_id(user_id: int) -> User | None:
#     async with async_session_maker() as session:
#         query = select(User).filter_by(id=user_id)
#         result = await session.execute(query)
#         return result.scalar_one_or_none()
#


async def update_user(user_id: int, values: dict):
    if not values:
        return
    async with async_session_maker() as session:
        query = update(User).where(User.id == user_id).values(**values)
        await session.execute(query)
        await session.commit()


async def delete_product(product_id: int):
    async with async_session_maker() as session:
        query = update(Product).where(Product.id == product_id).values(deleted_at=datetime.datetime.utcnow())
        await session.execute(query)
        await session.commit()


async def create_refresh_token(
        user_id: int,
        refresh_key: str,
        expires_at: datetime,
        session: AsyncSession,
) -> None:
    token = UserRefreshToken(
        user_id=user_id,
        refresh_key=refresh_key,
        expires_at=expires_at,
    )
    session.add(token)
    await session.commit()


async def get_refresh_token_by_key(key: str, session: AsyncSession) -> UserRefreshToken | None:
    user_token = await session.execute(
        select(UserRefreshToken)
        .options(joinedload(UserRefreshToken.user))
        .where(
            UserRefreshToken.refresh_key == key,
            UserRefreshToken.expires_at > datetime.datetime.utcnow(),
        )
    )

    return user_token.scalar_one_or_none()


async def add_product(
        title: str,
        price: float,
        session: AsyncSession,
        image_url: str = '',
        image_file: str = '',
) -> Product | None:
    product = Product(
        title=title,
        price=price,
        image_url=image_url,
        image_file=image_file
    )
    session.add(product)
    try:
        await session.commit()
        await session.refresh(product)
        return product
    except IntegrityError:
        await session.rollback()
        return None


async def add_comment(
        text_review: str,
        user_id: str,
        created_at: datetime.datetime.now(),
        session: AsyncSession,
) -> Comments | None:
    comment = Comments(
        text_review=text_review,
        user_id=user_id,
        created_at=created_at
    )
    session.add(comment)
    try:
        await session.commit()
        await session.refresh(comment)
        return comment
    except IntegrityError:
        await session.rollback()
        return None


async def fetch_comments(skip: int = 0, limit: int = 120) -> list[Comments]:
    async with async_session_maker() as session:
        query = select(Comments).offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()


async def fetch_products(session: AsyncSession, offset=0, limit=12, q='') -> list:
    if q:
        query = select(Product).filter(
            Product.title.icontains(q),
            Product.deleted_at == None
            ).offset(offset).limit(limit)
    else:
        query = select(Product).filter(Product.deleted_at == None).offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all() or []


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    query = select(Product).filter(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_or_create(session: AsyncSession, model, only_get=False, **kwargs):
    query = select(model).filter_by(**kwargs)
    instance = await session.execute(query)
    instance = instance.scalar_one_or_none()
    if instance or only_get:
        return instance
    instance = model(**kwargs)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return instance


async def fetch_order_products(session: AsyncSession, order_id: int) -> list:
    query = select(OrderProduct).filter(OrderProduct.order_id == order_id,
                                        OrderProduct.quantity > 0,
                                        OrderProduct.price > 0).options(joinedload(OrderProduct.product))
    result = await session.execute(query)
    return result.scalars().all() or []


async def get_order_product(session: AsyncSession, order_id: int, product_id: int) -> OrderProduct | None:
    query = select(OrderProduct).filter(
        OrderProduct.order_id == order_id,
        OrderProduct.id == product_id
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def decrease_product_quantity_in_order(session: AsyncSession, order_id: int, product_id: int):
    order_product = await session.execute(
        select(OrderProduct).filter(OrderProduct.order_id == Order.id, OrderProduct.product_id == Product.id)
    )
    order_product = order_product.scalar_one_or_none()

    if order_product:
        if order_product.quantity > 1:
            order_product.quantity -= 1
        else:
            await session.delete(order_product)

        await session.commit()


async def delete_order_product(product_id: int):
    async with async_session_maker() as session:
        query = delete(OrderProduct).where(OrderProduct.id == product_id)
        await session.execute(query)
        await session.commit()


async def get_open_order(session: AsyncSession, user_id: int):
    open_order = await session.execute(
        select(Order).filter(Order.user_id == user_id, Order.is_closed == False)
    )
    open_order = open_order.scalar_one_or_none()
    return open_order

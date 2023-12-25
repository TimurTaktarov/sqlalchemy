import asyncio
import datetime

from sqlalchemy import insert, select, update, delete
from pprint import pprint
from models import User, Order
from database import async_session_maker


# FIRST CRUD FOR USERS
# async def create_user(
#         name: str,
#         login: str,
#         password: str,
#         age: int,
#         nickname: str = None,
#         notes: str = None,
# ):
#     # await asyncio.sleep(2)
#     # print(9999999999)
#     async with async_session_maker() as session:
#         query = insert(User).values(
#             name=name,
#             login=login,
#             password=password,
#             age=age,
#             nickname=nickname,
#             notes=notes,
#         ).returning(User.id, User.created_at, User.login)
#         print(query)
#         data = await session.execute(query)
#         await session.commit()
#         print(tuple(data))
#
#
# async def fetch_users(skip: int = 0, limit: int = 10) -> list[User]:
#     async with async_session_maker() as session:
#         query = select(User).offset(skip).limit(limit)
#         result = await session.execute(query)
#         # print(query)
#         # print(type(result.scalars().all()))
#         # print(result.scalars().all()[0].name)
#         pprint(result.scalars().all()[0].__dict__)
#         return result.scalars().all()
#
#
# async def get_user_by_id(user_id: int) -> User | None:
#     async with async_session_maker() as session:
#         query = select(User).filter_by(id=user_id)
#         result = await session.execute(query)
#         pprint(result.scalar_one_or_none())
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
#         print(tuple(result))
#         # print(query)
#
#
# async def delete_user(user_id: int):
#     async with async_session_maker() as session:
#         query = delete(User).where(User.id == user_id)
#         await session.execute(query)
#         await session.commit()
#         print(query)
#
#
# async def main():
#     await asyncio.gather(
#         # create_user(
#         #     name='Misha',
#         #     login='Zuzhap-3',
#         #     password='007',
#         #     age=25,
#         #     nickname='loloscha',
#         # ),
#         # fetch_users(limit=10),
#         # get_user_by_id(1),
#         # update_user(6, {'name': 'Alex-23', 'age': 69})
#         delete_user(6)
#     )
#
#
# asyncio.run(main())


# # SECOND CRUD FOR ORDERS

async def create_order(
        quantity: int,
        price: float,
        customer: int,
        notes: str = None,
):
    # await asyncio.sleep(2)
    # print(9999999999)
    async with async_session_maker() as session:
        query = insert(Order).values(
            quantity=quantity,
            price=price,
            customer=customer,
            notes=notes,
        ).returning(Order.id, Order.created_at, Order.customer)
        print(query)
        data = await session.execute(query)
        await session.commit()
        print(tuple(data))


async def fetch_orders(skip: int = 0, limit: int = 10) -> list[Order]:
    async with async_session_maker() as session:
        query = select(Order).offset(skip).limit(limit)
        result = await session.execute(query)
        # print(query)
        # print(type(result.scalars().all()))
        print(result.scalars().all()[0].price)
        # print(result.scalars().all()[0].__dict__)
        return result.scalars().all()


async def get_order_by_id(order_id: int) -> Order | None:
    async with async_session_maker() as session:
        query = select(Order).filter_by(id=order_id)
        result = await session.execute(query)
        print(result.scalar_one_or_none())
        return result.scalar_one_or_none()


async def update_order(order_id: int, values: dict):
    if not values:
        return
    async with async_session_maker() as session:
        query = update(Order).where(Order.id == order_id).values(**values)
        result = await session.execute(query)
        await session.commit()
        # print(tuple(result))
        print(query)


async def delete_order(order_id: int):
    async with async_session_maker() as session:
        query = delete(Order).where(Order.id == order_id)
        await session.execute(query)
        await session.commit()
        print(query)


async def main():
    await asyncio.gather(
        # create_order(
        #     quantity=10,
        #     price=129.9,
        #     customer=1,
        #     notes='Lucky',
        # ),
        # fetch_orders(skip=0)
        # get_order_by_id(1),
        # update_order(1, {'customer': 5, 'notes': 'Milk'})
        delete_order(1)
    )


asyncio.run(main())

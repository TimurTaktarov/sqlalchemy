from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped,  relationship
from sqlalchemy.orm import mapped_column

from database import Base


# https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html

class BaseInfoMixin:
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    notes: Mapped[Optional[str]]


class User(BaseInfoMixin, Base):
    __tablename__ = "users"

    name: Mapped[str]
    login: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    password: Mapped[str]
    nickname: Mapped[Optional[str]]
    is_active: Mapped[bool] = mapped_column(default=True)
    age: Mapped[int]
    money: Mapped[int] = mapped_column(default=0)

    orders = relationship('Order', back_populates='user')

    def __repr__(self) -> str:
        return f'User {self.name} -> #{self.id}'


class Address(BaseInfoMixin, Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    country: Mapped[Optional[str]] = mapped_column(String(5), index=True)
    region: Mapped[str]
    street: Mapped[Optional[str]] = mapped_column(default='Ivana Franka Street')

    def __repr__(self) -> str:
        return f'Country {self.country} -> #{self.id}'


class Order(BaseInfoMixin, Base):
    __tablename__ = 'orders'

    quantity: Mapped[int]
    price: Mapped[float]
    customer: Mapped[int] = mapped_column(ForeignKey('users.id'))

    user = relationship('User', back_populates='orders')

    def __repr__(self) -> str:
        return f'Order {self.id} -> #{self.customer}'

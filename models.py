from typing import Optional

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database import Base


# https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    login: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    password: Mapped[str]
    nickname: Mapped[Optional[str]]
    is_active: Mapped[bool] = mapped_column(default=True)
    age: Mapped[int]
    money: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f'User {self.name} -> #{self.id}'


class Address(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    country: Mapped[Optional[str]] = mapped_column(String(5), index=True)
    region: Mapped[str]
    street: Mapped[Optional[str]] = mapped_column(default='Ivana Franka Street')

    def __repr__(self) -> str:
        return f'Country {self.country} -> #{self.id}'

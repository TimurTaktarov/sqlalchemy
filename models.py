from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, ForeignKey, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column

from database import Base


# https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html
class BaseInfoMixin:
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    notes: Mapped[Optional[str]]


class Comments(BaseInfoMixin, Base):
    __tablename__ = "comments"

    text_review: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    comments = relationship('User', back_populates='comments')


class User(BaseInfoMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(50), index=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    hashed_password: Mapped[str]
    user_uuid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)
    is_active: Mapped[bool] = mapped_column(default=True)
    verified_at: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=True)
    avatar: Mapped[str] = mapped_column(default='', nullable=True)

    tokens = relationship('UserRefreshToken', back_populates='user')
    orders = relationship('Order', back_populates='user')
    comments = relationship('Comments', back_populates='comments')
    def __repr__(self) -> str:
        return f'User {self.name} -> #{self.id}'


class UserRefreshToken(BaseInfoMixin, Base):
    __tablename__ = 'refresh_tokens'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    refresh_key: Mapped[str]
    expires_at: Mapped[datetime]

    user = relationship('User', back_populates='tokens')


class Product(BaseInfoMixin, Base):
    __tablename__ = 'products'

    title: Mapped[str]
    price: Mapped[float]
    image_url: Mapped[str] = mapped_column(default='', nullable=True)
    image_file: Mapped[str] = mapped_column(default='', nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    products = relationship('OrderProduct', back_populates='product')

    def __str__(self):
        return f'Product {self.title} - #{self.id}'


class Order(BaseInfoMixin, Base):
    __tablename__ = 'orders'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    is_closed: Mapped[bool] = mapped_column(default=False)

    user = relationship('User', back_populates='orders', lazy=False)


class OrderProduct(BaseInfoMixin, Base):
    __tablename__ = 'order_products'

    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    price: Mapped[float] = mapped_column(default=0.0)
    quantity: Mapped[int] = mapped_column(default=0)

    product = relationship('Product', back_populates='products')

    def __str__(self):
        return f'OrderProduct {self.product.title} - #{self.id}, {self.quantity} >> {self.price} = {self.quantity * self.price}'

    __repr__ = __str__

import uuid
from typing import Optional, List

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from fastapi.responses import FileResponse
from starlette import status
import datetime

from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
import dao

from pathlib import Path

from library.email_sender import send_email_verification, send_email_order
from library.security_lib import PasswordEncrypt, SecurityHandler
from models import Order, OrderProduct, Comments

web_router = APIRouter(
    prefix='',
    tags=['WEB'],
    include_in_schema=False,
)

templates = Jinja2Templates(directory=Path(__file__).parent.parent / 'templates')


class UserCreateForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: list = []
        self.email: Optional[str] = None
        self.name: Optional[str] = None
        self.password: Optional[str] = None
        self.password_confirm: Optional[str] = None
        self.hashed_password: str = ''
        self.avatar: str = ''

    async def load_data(self):
        form = await self.request.form()
        self.email = form.get('email')
        self.name = form.get('name') or ''
        self.password = form.get('password')
        self.password_confirm = form.get('password_confirm')
        self.avatar = form.get('avatar')

    async def is_valid(self, session: AsyncSession, check_email=True):
        if check_email:
            if not self.email or '@' not in self.email:
                self.errors.append('Please? enter valid email')

        maybe_user = await dao.get_user_by_email(self.email, session)
        if maybe_user:
            self.errors.append('User with this email  already exists')

        if not self.name or len(str(self.name)) < 3:
            self.errors.append('Please? enter valid name')
        if not self.password or len(str(self.password)) < 8:
            self.errors.append('Please? enter password at least 8 symbols')
        if self.password != self.password_confirm:
            self.errors.append('Confirm password did not match!')
        if not self.errors:
            return True
        return False


@web_router.get('/cart')
async def cart(request: Request, user=Depends(SecurityHandler.get_current_user_web),
               session: AsyncSession = Depends(get_async_session)):
    if user:
        order = await dao.get_or_create(session=session, model=Order, user_id=user.id, is_closed=False)
        cart = await dao.fetch_order_products(session, order.id)

        subtotal = sum([product.price * product.quantity for product in cart])

        context = {
            'request': request,
            'user': user,
            'cart': cart,
            'subtotal': subtotal,
            'shipping': subtotal * 0.05,
            'total': subtotal + subtotal * 0.05,
        }

        response = templates.TemplateResponse('cart.html', context=context)
        return await SecurityHandler.set_cookies_web(user, response)
    else:
        redirect_url = request.url_for('index')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return await SecurityHandler.set_cookies_web(user, response)


@web_router.post('/cart/increase_quantity/{cart_product_id}')
async def increase_product_quantity_in_cart(
        cart_product_id: int,
        request: Request,
        user=Depends(SecurityHandler.get_current_user_web),
        session: AsyncSession = Depends(get_async_session)):
    if user:
        order = await dao.get_or_create(session=session, model=Order, user_id=user.id, is_closed=False)
        order_product = await dao.get_order_product(session, order.id, cart_product_id)
        if order_product:
            order_product.quantity += 1
            session.add(order_product)
            await session.commit()
    redirect_url = request.url_for('cart')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.post('/cart/decrease_quantity/{cart_product_id}')
async def decrease_product_quantity_in_cart(
        cart_product_id: int,
        request: Request,
        user=Depends(SecurityHandler.get_current_user_web),
        session: AsyncSession = Depends(get_async_session)):
    if user:
        order = await dao.get_or_create(session=session, model=Order, user_id=user.id, is_closed=False)
        order_product = await dao.get_order_product(session, order.id, cart_product_id)
        if order_product and order_product.quantity > 0:
            order_product.quantity -= 1
            if order_product.quantity == 0:
                await dao.delete_order_product(cart_product_id)
            else:
                session.add(order_product)
                await session.commit()
    redirect_url = request.url_for('cart')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.post('/cart/delete_product_from_cart/{cart_product_id}')
async def delete_product_in_cart(
        cart_product_id: int,
        request: Request,
        user=Depends(SecurityHandler.get_current_user_web),
        session: AsyncSession = Depends(get_async_session)):
    if user:
        order = await dao.get_or_create(session=session, model=Order, user_id=user.id, is_closed=False)
        order_product = await dao.get_order_product(session, order.id, cart_product_id)
        if order_product:
            await dao.delete_order_product(cart_product_id)
            session.add(order_product)
            await session.commit()
    redirect_url = request.url_for('cart')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.post('/close-order')
async def close_order(request: Request,
                      background_tasks: BackgroundTasks,
                      user=Depends(SecurityHandler.get_current_user_web),
                      session: AsyncSession = Depends(get_async_session),

                      ):
    if user:
        order: Order = await dao.get_or_create(session=session, model=Order, user_id=user.id, is_closed=False)
        cart = await dao.fetch_order_products(session, order.id)
        if cart:
            order.is_closed = True
            session.add(order)
            await session.commit()
            await session.close()
            background_tasks.add_task(
                send_email_order,
                user_email=user.email,
                user_name=user.name,
                order=order,
                cart=cart,
            )
    redirect_url = request.url_for('index')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.get('/signup', description='get form for registration')
@web_router.post('/signup', description='fill out the registration form')
async def web_register(
        request: Request,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
        avatar: str = Form(None),
):
    if request.method == 'GET':
        return templates.TemplateResponse('registration.html', context={'request': request})

    new_user_form = UserCreateForm(request)
    await new_user_form.load_data()
    if await new_user_form.is_valid(session):
        hashed_password = await PasswordEncrypt.get_password_hash(new_user_form.password)

        is_first_user = await dao.is_first_user(session)

        saved_user = await dao.create_user(
            name=new_user_form.name,
            email=new_user_form.email,
            hashed_password=hashed_password,
            is_admin=is_first_user,
            session=session,
            avatar=avatar,
        )
        background_tasks.add_task(
            send_email_verification,
            user_email=saved_user.email,
            user_uuid=saved_user.user_uuid,
            user_name=saved_user.name,
            host=request.base_url,
        )
        redirect_url = request.url_for('index')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return await SecurityHandler.set_cookies_web(saved_user, response)
    else:
        return templates.TemplateResponse('registration.html', context=new_user_form.__dict__)


@web_router.get('/login', description='get form for login')
@web_router.post('/login', description='fill out the login form')
async def user_login_web(
        request: Request,
        login: EmailStr = Form(None),
        password: str = Form(None),
        session: AsyncSession = Depends(get_async_session),
):
    if request.method == 'GET':
        return templates.TemplateResponse('login.html', context={'request': request})
    user, is_password_correct = await SecurityHandler.authenticate_user_web(login, password or '', session)
    if all([user, is_password_correct]):
        redirect_url = request.url_for('index')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return await SecurityHandler.set_cookies_web(user, response)
    return templates.TemplateResponse('login.html', context={'request': request})


@web_router.get('/logout', description='log out')
async def user_logout_web(request: Request):
    response = templates.TemplateResponse('login.html', context={'request': request})
    response.delete_cookie(key='token')
    return response


@web_router.get('/account_update', description='update user datas')
async def update_user_form(request: Request, user=Depends(SecurityHandler.get_current_user_web)):
    return templates.TemplateResponse('profile.html', context={'request': request, 'user': user})


@web_router.post('/account_update', description='update user datas')
async def update_user_data(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
        user=Depends(SecurityHandler.get_current_user_web),
):
    user_update_data = UserCreateForm(request)
    await user_update_data.load_data()
    if user:

        if await user_update_data.is_valid(session, check_email=False):
            hashed_password = await PasswordEncrypt.get_password_hash(user_update_data.password)

            update_user = await dao.update_user(user_id=user.id, values={
                'hashed_password': hashed_password,
                'avatar': user_update_data.avatar,
                'name': user_update_data.name,

            })
            redirect_url = request.url_for('index')
            response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
            return await SecurityHandler.set_cookies_web(update_user, response)


@web_router.get('/add-review')
async def add_review_get(request: Request, user=Depends(SecurityHandler.get_current_user_web)):
    if not user:
        response = templates.TemplateResponse('login.html', context={'request': request})
        response.delete_cookie(key='token')
        return response

    context = {
        'request': request,
        'user': user
    }
    response = templates.TemplateResponse('review.html', context=context)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.post('/add-review', description='Add comments')
async def add_reviews(request: Request,
                      user=Depends(SecurityHandler.get_current_user_web),
                      session: AsyncSession = Depends(get_async_session),
                      text: str = Form()):
    if not user:
        response = templates.TemplateResponse('login.html', context={'request': request})
        response.delete_cookie(key='token')
        return response
    if user:
        comment = await dao.add_comment(session=session,
                                        user_id=user.id,
                                        created_at=datetime.datetime.now(),
                                        text_review=text)
        session.add(comment)
        await session.commit()

    redirect_url = request.url_for('all_comments')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.get('/get-reviews', description='Getting all comments')
async def all_comments(request: Request, user=Depends(SecurityHandler.get_current_user_web)):

    review_all: List[Comments] = await dao.fetch_comments()

    users = await dao.fetch_users()

    user_names = {user.id: user.name for user in users}

    context = {
        'request': request,
        'all_comments': review_all,
        'user_names': user_names,
        'user': user
    }

    response = templates.TemplateResponse('all_comments.html', context=context)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.get('/add-product', description='add-product')
async def add_product(request: Request, user=Depends(SecurityHandler.get_current_user_web)):
    if not user or not user.is_admin:
        response = templates.TemplateResponse('login.html', context={'request': request})
        response.delete_cookie(key='token')
        return response

    context = {
        'request': request,
        'user': user,
    }
    response = templates.TemplateResponse('add-product.html', context=context)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.post('/delete-product/{product_id}')
async def admin_delete_product(
        product_id: int,
        request: Request,
        user=Depends(SecurityHandler.get_current_user_web),
        session: AsyncSession = Depends(get_async_session)):
    if user.is_admin:
        product = await dao.get_product(session, product_id)
        if product:
            await dao.delete_product(product_id)
            session.add(product)
    redirect_url = request.url_for('index')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.post('/add-product', description='add-product')
async def add_product_post(
        request: Request,
        user=Depends(SecurityHandler.get_current_user_web),
        title: str = Form(),
        price: float = Form(),
        image_url: str = Form(None),
        image_file: UploadFile = File(None),
        session: AsyncSession = Depends(get_async_session),
):
    if not user or not user.is_admin:
        response = templates.TemplateResponse('login.html', context={'request': request})
        response.delete_cookie(key='token')
        return response

    saved_file_name = ''
    if image_file:
        extention = image_file.filename.split(".")[-1]
        if extention in {'jpg', 'png', 'jpeg'}:
            saved_file_name = f'{uuid.uuid4()}.{extention}'
            with open(f'static/product_images/{saved_file_name}', 'wb') as prod_file:
                prod_file.write(await image_file.read())
    await dao.add_product(
        title=title,
        price=price,
        image_url=image_url,
        image_file=saved_file_name,
        session=session,
    )

    redirect_url = request.url_for('index')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.get('/file/{filename}')
async def download_file(filename: str):
    return FileResponse(path=f'static/product_images/{filename}', filename=f'123{filename}',
                        media_type='multipart/form-data')


@web_router.post('/shop/add/{product_id}')
async def add_product(product_id: int, request: Request,
                      user=Depends(SecurityHandler.get_current_user_web),
                      session: AsyncSession = Depends(get_async_session), ):
    if not user:
        redirect_url = request.url_for('user_login_web')
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return await SecurityHandler.set_cookies_web(user, response)

    product = await dao.get_product(session, product_id)

    if product:
        order = await dao.get_or_create(session=session, model=Order, user_id=user.id, is_closed=False)
        order_product: OrderProduct = await dao.get_or_create(session=session, model=OrderProduct, order_id=order.id,
                                                              product_id=product.id)
        order_product.quantity += 1
        order_product.price = product.price
        session.add(order_product)
        await session.commit()
        await session.refresh(order_product)

    redirect_url = request.url_for('index')
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.get('/')
@web_router.post('/')
async def index(request: Request, query: str = Form(None), search: str = Form(None),
                user=Depends(SecurityHandler.get_current_user_web),
                session: AsyncSession = Depends(get_async_session)):
    cart = []
    if user:
        order = await dao.get_or_create(session=session, model=Order, user_id=user.id, is_closed=False)
        cart = await dao.fetch_order_products(session, order.id)
    products = await dao.fetch_products(session, q=search or query)
    context = {
        'request': request,
        'user': user,
        'products': products,
        'cart': cart,
        'brands': ['Nike', 'Adidas', 'Jordan'],
    }

    response = templates.TemplateResponse('index.html', context=context)
    return await SecurityHandler.set_cookies_web(user, response)


@web_router.get('/TechnicalSupport')
async def tech_support(
        request: Request,
        user=Depends(SecurityHandler.get_current_user_web)):
    context = {
        'request': request,
        'user': user,
        'title': 'About our shop'
    }
    return templates.TemplateResponse('techsupport.html', context=context)

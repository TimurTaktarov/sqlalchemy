from fastapi import APIRouter, Depends
from library.security_lib import SecurityHandler

router_public = APIRouter(
    prefix='/api/public/products',
    tags=['API', 'Products', 'Public']
)


router_private = APIRouter(
    prefix='/api/private/products',
    tags=['API', 'Products', 'Private'],
    dependencies=[Depends(SecurityHandler.oauth2_scheme), Depends(SecurityHandler.get_current_user)]
)


@router_public.get('/')
async def get_products():
    return {'products': 1000}


@router_private.get('/vip-products/')
async def get_products_private():
    return {'products': 500000}
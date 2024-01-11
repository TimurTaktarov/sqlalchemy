from fastapi import APIRouter

router = APIRouter(
    prefix='/api/products',
    tags=['API', 'Products']
)


@router.get('/')
async def get_products():
    return {'products': 1000}


@router.get('/vip-products/')
async def get_products_private():
    return {'products': 500000}
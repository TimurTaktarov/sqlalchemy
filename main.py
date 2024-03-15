from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sentry_sdk

from api import api_router_user, general_routers, api_router_auth
from web import web_router

sentry_sdk.init(
    dsn="https://ee89d63567fc596d6d76ee09d80cafc0@o4506246629294080.ingest.sentry.io/4506246631784448",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)
app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')
app.mount('/static/product_images', StaticFiles(directory='static/product_images'), name='product_images')

app.include_router(api_router_user.router)
app.include_router(general_routers.router_public)
app.include_router(general_routers.router_private)
app.include_router(api_router_auth.public_router)

app.include_router(web_router.web_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', reload=True, host='127.0.0.1', port=9000)

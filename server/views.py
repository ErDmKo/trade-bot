import aiohttp_jinja2
from aiohttp import web
from .utils import dumps

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}
    

async def pairs(request):
    info = await request.app['pubapi'].call('ticker')
    return web.json_response(info, dumps = dumps)

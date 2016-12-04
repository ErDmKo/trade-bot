import aiohttp_jinja2
from aiohttp import web

@aiohttp_jinja2.template('index.html')
async def index(request):
    info = await request.app['pubapi'].call('ticker')
    return {
        'info': info
    }

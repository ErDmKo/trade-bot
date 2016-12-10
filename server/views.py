import aiohttp_jinja2
import aiohttp
from aiohttp import web
from .utils import dumps

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}
    

async def pairs(request):
    info = await request.app['pubapi'].call('ticker')
    return web.json_response(info, dumps = dumps)

async def ws_pairs(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app['pair_socket'] = ws
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                ws.send_str(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

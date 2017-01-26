import aiohttp_jinja2
import aiohttp
from aiohttp import web
from .utils import dumps
from . import db

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}
    

async def pairs(request):
    print(request.headers)
    info = await request.app['pubapi'].call('ticker')
    return web.json_response(info, dumps = dumps)

async def order(request):

    data = await request.json()
    async with request.app['db'].acquire() as conn:
        await db.add_order(conn, data['price'], data['pair'])
        cursor = await conn.execute(db.order.select())
        orders = await cursor.fetchall()
        return web.json_response({
            'orders': [dict(q) for q in orders]
        }, dumps = dumps)

async def ws_balance(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app['balance_socket'] = ws

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'connect':
                info = await request.app['privapi'].call('getInfo')
                ws.send_json(info, dumps = dumps)
            elif msg.data == 'close':
                await ws.close()
            else:
                print(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())


async def ws_pairs(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app['pair_socket'] = ws
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'connect':
                info = await request.app['pubapi'].call('ticker')
                ws.send_json(info, dumps = dumps)
            elif msg.data == 'close':
                await ws.close()
            else:
                print(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

async def ws_order_book(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app['depth_socket'] = ws
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'connect':
                info = await request.app['pubapi'].call('depth')
                ws.send_json(info, dumps = dumps)
            elif msg.data == 'close':
                await ws.close()
            else:
                print(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

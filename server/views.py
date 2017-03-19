import aiohttp_jinja2
import asyncio
import aiohttp
from aiohttp import web
from .utils import dumps, handle_socket
from . import db

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}
    

async def pairs(request):
    print(request.headers)
    info = await request.app['pubapi'].call('ticker')
    return web.json_response(info, dumps = dumps)

async def delete_orders(request):
    async with request.app['db'].acquire() as conn:
        await conn.execute(db.order.delete().where(
            db.order.c.id==request.GET.get('id')
        ))
        cursor = await conn.execute(db.order.select())
        orders = await cursor.fetchall()
        return web.json_response({
            'orders': [dict(q) for q in orders]
        }, dumps = dumps)

async def get_orders(request):
    async with request.app['db'].acquire() as conn:
        cursor = await conn.execute(db.order.select().limit(10))
        orders = await cursor.fetchall()
        return web.json_response({
            'orders': [dict(q) for q in orders]
        }, dumps = dumps)
    
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
    channel = request.app['socket_channels']['balance_socket']
    channel.append(ws)
    return await handle_socket(ws, request.app['privapi'], 'getInfo') 

async def ws_pairs(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    channel = request.app['socket_channels']['pair_socket']
    channel.append(ws)
    return await handle_socket(ws, request.app['pubapi'], 'ticker') 

async def ws_order_book(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    channel = request.app['socket_channels']['depth_socket']
    channel.append(ws)
    return await handle_socket(ws, request.app['pubapi'], 'depth') 

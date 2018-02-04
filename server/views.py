import aiohttp_jinja2
import sqlalchemy as sa
import asyncio
import aiohttp
from aiohttp import web
from .utils import dumps, handle_socket
from . import db

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}
    

async def pairs(request):
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

async def order_info(request):
    async with request.app['db'].acquire() as conn:
        cursor = await conn.execute(db.order
                .select()
                .where(db.order.c.id == request.match_info['id'])
                .order_by(db.order.c.pub_date.desc())
                .limit(30)
            )
        orders = await cursor.fetchall()
        orders = [dict(q) for q in orders]
        return web.json_response(orders[0], dumps=dumps)

async def get_orders(request):
    filterInfo = request.GET
    limit = 30
    offset = 0
    args = []
    if filterInfo.get('pair'):
        args.append(db.order.c.pair == filterInfo.get('pair'))

    if filterInfo.get('parent'):
        args.append(db.order.c.extra['parent'].astext == filterInfo.get('parent'))

    if filterInfo.get('limit'):
        try:
            limit = int(filterInfo.get('limit'))
        except ValueError as e:
            pass

    if filterInfo.get('offset'):
        try:
            offset = int(filterInfo.get('offset'))
        except ValueError as e:
            pass

    async with request.app['db'].acquire() as conn:
        cursor = await conn.execute(db.order
                .select()
                .where(sa.sql.and_(*args))
                .order_by(db.order.c.pub_date.desc())
                .limit(limit)
                .offset(offset)
            )
        orders = await cursor.fetchall()
        cursor = await conn.execute(
            db.order.select()
                .with_only_columns([
                    sa.sql.func.count(db.order.c.id).label('total')
                ])
                .where(sa.sql.and_(*args))
            )
        meta = await cursor.fetchall()
        return web.json_response({
            'orders': [dict(q) for q in orders],
            'meta':  dict(meta[0])
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

async def ws_trade_log(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    channel = request.app['socket_channels']['log']
    channel.append(ws)
    return await handle_socket(ws) 

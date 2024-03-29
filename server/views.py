import aiohttp_jinja2
import sqlalchemy as sa
import datetime
from aiohttp import web
from .utils import dumps, handle_socket
from . import db


@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}


async def pairs(request):
    info = await request.app['pubapi'].call('ticker')
    return web.json_response(info, dumps=dumps)


async def delete_orders(request):
    async with request.app['db'].acquire() as conn:
        await conn.execute(db.order.delete().where(
            db.order.c.id == request.GET.get('id')
        ))
        cursor = await conn.execute(db.order.select())
        orders = await cursor.fetchall()
        return web.json_response({
            'orders': [dict(q) for q in orders]
        }, dumps=dumps)


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


async def get_history(request):
    filterInfo = request.GET
    limit = 10
    sampling = False
    offset = 0
    group_by = False
    args = []

    if filterInfo.get('group'):
        group_by = filterInfo['group']

    if filterInfo.get('from'):
        args.append(lambda history: history.c.pub_date >=
                    filterInfo.get('from'))
    else:
        args.append(lambda history: history.c.pub_date >=
                    datetime.now() - datetime.timedelta(minutes=1))

    if filterInfo.get('to'):
        args.append(lambda history: history.c.pub_date <= filterInfo.get('to'))

    if filterInfo.get('pair'):
        args.append(lambda history: history.c.pair == filterInfo.get('pair'))
    else:
        raise Exception('Pair is requried')

    async with request.app['db'].acquire() as conn:
        items = await db.get_history(conn, group_by, args, limit, offset)
        return web.json_response({
            'history': [dict(q) for q in items],
        }, dumps=dumps)


async def get_orders(request):
    '''
    return web.json_response({
        "ok": 1
    })
    '''
    filterInfo = request.query
    limit = 30
    offset = 0
    args = []
    if filterInfo.get('pair'):
        args.append(db.order.c.pair == filterInfo.get('pair'))

    if filterInfo.get('parent'):
        args.append(
            db.order.c.extra['parent'].astext == filterInfo.get('parent'))

    if filterInfo.get('is_sell'):
        is_sell = None
        try:
            is_sell = int(filterInfo.get('is_sell'))
        except:
            pass
        if is_sell != None:
            args.append(db.order.c.is_sell == (is_sell == 1))

    if filterInfo.get('is_exceed'):
        exceed = None
        try:
            exceed = int(filterInfo.get('is_exceed'))
        except:
            pass
        if exceed != None:
            args.append(db.order.c.extra['is_exceed'].astext == (
                '0' if not exceed else '1'))

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

    if not request.app.get('db'):
        raise Exception('No database connetion')

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
        }, dumps=dumps)


async def order(request):
    data = await request.json()
    async with request.app['db'].acquire() as conn:
        await db.add_order(conn, data['price'], data['pair'])
        cursor = await conn.execute(db.order.select())
        orders = await cursor.fetchall()
        return web.json_response({
            'orders': [dict(q) for q in orders]
        }, dumps=dumps)


async def ws_balance(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    channel = request.app['socket_channels']['balance_socket']
    channel.append(ws)
    return await handle_socket(ws, request.app, 'getInfo')


async def ws_pairs(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    channel = request.app['socket_channels']['pair_socket']
    channel.append(ws)
    return await handle_socket(ws, request.app, 'ticker')


async def ws_order_book(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    channel = request.app['socket_channels']['depth_socket']
    channel.append(ws)
    return await handle_socket(ws, request.app, 'depth')


async def ws_trade_log(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    channel = request.app['socket_channels']['log']
    channel.append(ws)
    return await handle_socket(ws, request.app, 'log')

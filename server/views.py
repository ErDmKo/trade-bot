import aiohttp_jinja2
import sqlalchemy as sa
import asyncio
import aiohttp
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB, REAL
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

async def get_history(request):
    filterInfo = request.GET
    limit = 30
    sampling = 100
    offset = 0
    group_by = False;
    args = []

    if filterInfo.get('group'):
        group_by = filterInfo['group']
        if group_by == 'minute':
            sampling = 10 
        if group_by == 'hour':
            sampling = 1 
        if group_by == 'days':
            sampling = 0.04
        if group_by == 'month':
            sampling = 0.001

    history = sa.tablesample(db.history, sa.func.system(sampling), seed=sa.cast('1', REAL))

    if filterInfo.get('from'):
        args.append(history.c.pub_date >= filterInfo.get('from'))

    if filterInfo.get('to'):
        args.append(history.c.pub_date <= filterInfo.get('to'))

    if filterInfo.get('pair'):
        args.append(history.c.pair == filterInfo.get('pair'))
    else:
        raise Exception('Pair is requried')
    ''' 
    SELECT 
        avg((CAST(((CAST((history_1.resp ->> 0) AS JSONB) -> 'asks'->0) ->> 0) AS REAL) 
        + CAST(((CAST((history_1.resp ->> 0) AS JSONB) -> 'bids'->0) ->> 0) AS REAL)) 
        / 2) AS price, 
        date_trunc('minute', history_1.pub_date) AS pub_date
    FROM 
        history AS history_1 TABLESAMPLE system(0.001)
    WHERE 
        history_1.pub_date >= '2018-05-11T00:00:00' 
        AND history_1.pub_date <= '2018-06-12T15:00:00' 
        AND history_1.pair = 'eth_btc' 
    GROUP BY 
        date_trunc('minute', history_1.pub_date) 
    ORDER BY 
        pub_date DESC
    LIMIT
        1000 
    OFFSET
        0;
    '''

    query = history.c.resp[0].astext.cast(JSONB)['asks'][0][0].astext.cast(REAL)
    query = query + history.c.resp[0].astext.cast(JSONB)['bids'][0][0].astext.cast(REAL)
    query = query / 2

    if (group_by):
        query = sa.func.avg(query)
    
    async with request.app['db'].acquire() as conn:
        date = history.c.pub_date
        collums = [query.label('price')]
        if group_by:
            date = sa.func.date_trunc(group_by, history.c.pub_date).label('pub_date')
            collums += [date, sa.func.count().label('count')]

        query = select(collums) \
            .where(sa.sql.and_(*args)) \
            .order_by(date.desc())

        if group_by:
            query = query \
                .group_by(date)
        else:
            query = query \
                .limit(limit) \
                .offset(offset)
        cursor = await conn.execute(query)
        items = await cursor.fetchall()
        return web.json_response({
            'history': [dict(q) for q in items],
        }, dumps = dumps)


async def get_orders(request):
    filterInfo = request.GET
    limit = 30
    offset = 0
    args = []
    if filterInfo.get('pair'):
        args.append(db.order.c.pair == filterInfo.get('pair'))

    if filterInfo.get('parent'):
        args.append(db.order.c.extra['parent'].astext == filterInfo.get('parent'))

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
            args.append(db.order.c.extra['is_exceed'].astext == ('0' if not exceed else '1'))

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

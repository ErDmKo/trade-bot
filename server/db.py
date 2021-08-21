import sqlalchemy as sa
import contextlib
from sqlalchemy.dialects.postgresql import JSONB, REAL
from sqlalchemy.sql import select
import aiopg.sa
import asyncio
import pathlib
import sys
from .utils import load_config, DecimalEncoder
import logging
logger = logging.getLogger(__name__)

meta = sa.MetaData()


history = sa.Table(
    'history', meta,
    sa.Column('id', sa.Integer, nullable=False, primary_key=True),
    sa.Column('pub_date', sa.DateTime, default=sa.sql.func.now(), nullable=False),
    sa.Column('pair', sa.String(200), nullable=False),
    sa.Column('resp', JSONB, nullable=False),
)
demo_order = sa.Table(
    'demo_order', meta,
    sa.Column('id', sa.Integer, nullable=False, primary_key=True),
    sa.Column('pub_date', sa.DateTime, default=sa.sql.func.now(), nullable=False),
    sa.Column('price', sa.Float, nullable=False),
    sa.Column('amount', sa.Float, nullable=False),
    sa.Column('extra', JSONB, nullable=False),
    sa.Column('pair', sa.String(200), nullable=False),
    sa.Column('api', JSONB, nullable=True),
    sa.Column('is_sell', sa.Boolean(), nullable=False),
)

''' 

EXPLAIN ANALYZE SELECT 
    avg((CAST(((CAST((history_1.resp ->> 0) AS JSONB) -> 'asks'->0) ->> 0) AS REAL) 
    + CAST(((CAST((history_1.resp ->> 0) AS JSONB) -> 'bids'->0) ->> 0) AS REAL)) 
    / 2) AS price, 
    date_trunc('minute', history_1.pub_date) AS pub_date
FROM 
    history AS history_1 TABLESAMPLE system(1)
WHERE 
    history_1.pub_date >= '2018-06-26T17:24:19.814Z' 
    AND history_1.pub_date <= '2018-06-26T18:24:19.816Z' 
    AND history_1.pair = 'btc_usd' 
GROUP BY 
    date_trunc('minute', history_1.pub_date) 
ORDER BY 
    pub_date DESC
LIMIT
    1000 
OFFSET
    0;
'''

async def get_history(conn, group_by=False, args=[], limit=10, offset=0):

    sampling = False
    if group_by == 'minute':
        sampling = 0 
    if group_by == 'hour':
        sampling = 0.3
    if group_by == 'day':
        sampling = 0.04
    if group_by == 'week':
        sampling = 0.01
    if group_by == 'month':
        sampling = 0.001

    if sampling:
        table = sa.tablesample(history, sa.func.system(sampling), seed=sa.cast('1', REAL))
    else:
        table = history

    args = [arg(table) for arg in args]

    query = table.c.resp[0].astext.cast(JSONB)['asks'][0][0].astext.cast(REAL)
    query = query + table.c.resp[0].astext.cast(JSONB)['bids'][0][0].astext.cast(REAL)
    query = query / 2

    if (group_by):
        query = sa.func.avg(query)

    date = table.c.pub_date
    collums = [query.label('price')]
    if group_by:
        date = sa.func.date_trunc(group_by, table.c.pub_date).label('pub_date')
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
    return items

order = sa.Table(
    'order', meta,
    sa.Column('id', sa.Integer, nullable=False, primary_key=True),
    sa.Column('pub_date', sa.DateTime, default=sa.sql.func.now(), nullable=False),
    sa.Column('price', sa.Float, nullable=False),
    sa.Column('amount', sa.Float, nullable=False),
    sa.Column('extra', JSONB, nullable=False),
    sa.Column('pair', sa.String(200), nullable=False),
    sa.Column('api', JSONB, nullable=True),
    sa.Column('is_sell', sa.Boolean(), nullable=False),
)

def sync_engine(conf):
    return sa.create_engine(
        'postgresql://{user}:{password}@{host}:{port}/{database}'.format(**conf)
    )
    
async def get_engine(conf, loop):
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=int(conf['port']),
        minsize=int(conf['minsize']),
        maxsize=int(conf['maxsize']),
        loop=loop)
    return engine
    
async def init_pg(app,  tryNo=None):
    if not tryNo:
        tryNo = 1
    try:
        engine = await get_engine(app['config']['postgres'], app.loop)
        app['db'] = engine
    except Exception as e:
        if tryNo > 5:
            raise e
        await asyncio.sleep(tryNo)
        await init_pg(app, tryNo + 1)

async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()

async def add_order(conn, price, pair, amount, is_sell, api):
    result = await conn.execute(
        order.insert().values(
            price = price,
            pair = pair,
            amount = amount,
            is_sell = is_sell,
            api = api
        )
    )
    result_info = await result.first()
    logger.info(result_info)

def command_fn(command):
    logger.info('{} - undefined'.format(command))

async def main_test(loop):
    conf = load_config()
    engine = sync_engine(conf['postgres'])
    if len(sys.argv) >= 2:
        command = sys.argv[2]
        if command in ['drop', 'create']:
            table = sys.argv[3]
            getattr(meta, '{}_all'.format(command))(engine, tables=[meta.tables.get(table)])
        elif command == 'delete':
            table = sys.argv[3]
            with contextlib.closing(engine.connect()) as con:
                trans = con.begin()
                table = sys.argv[3]
                table = meta.tables.get(table)
                con.execute(table.delete())
                trans.commit()
        else:
            getattr(meta, command, lambda engine: command_fn(command))(engine)

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

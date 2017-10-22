import sqlalchemy as sa
import contextlib
from sqlalchemy.dialects.postgresql import JSONB
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
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
        loop=loop)
    return engine
    
async def init_pg(app):
    engine = await get_engine(app['config']['postgres'], app.loop)
    app['db'] = engine

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

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import aiopg.sa
import asyncio
import pathlib
import sys
from .utils import load_config

meta = sa.MetaData()


history = sa.Table(
    'history', meta,
    sa.Column('id', sa.Integer, nullable=False, primary_key=True),
    sa.Column('pub_date', sa.DateTime, default=sa.sql.func.now(), nullable=False),
    sa.Column('pair', sa.String(200), nullable=False),
    sa.Column('resp', JSONB, nullable=False),
)
'''
history_orders = sa.Table(
    'history_orders', meta,
    sa.Column('id', sa.Integer, nullable=False, primary_key=True),
    sa.Column('price', sa.Float, nullable=False),
    sa.Column('volume', sa.Float, nullable=False),
)
'''

order = sa.Table(
    'order', meta,
    sa.Column('id', sa.Integer, nullable=False, primary_key=True),
    sa.Column('pub_date', sa.DateTime, nullable=False),
    sa.Column('price', sa.Float, nullable=False),
    sa.Column('pair', sa.String(200), nullable=False),
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

async def add_order(conn, price, pair):
    result = await conn.execute(
        order.insert().values(price=price, pair=pair)
    )
    result_info = await result.first()
    print(result_info)

def command_fn(command):
    print('{} - undefined'.format(command))

async def main_test(loop):
    conf = load_config(str(pathlib.Path('.') / 'config' / 'base.yaml'))
    engine = sync_engine(conf['postgres'])
    if len(sys.argv) >= 2:
        command = sys.argv[2]
        getattr(meta, command, lambda engine: command_fn(command))(engine)

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

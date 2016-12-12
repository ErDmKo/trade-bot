import sqlalchemy as sa
import aiopg.sa

meta = sa.MetaData()


order = sa.Table(
    'order', meta,
    sa.Column('id', sa.Integer, nullable=False),
    sa.Column('pub_date', sa.Date, nullable=False),
    sa.Column('price', sa.Float, nullable=False),
    sa.Column('pair', sa.String(200), nullable=False),

    sa.PrimaryKeyConstraint('id', name='choice_id_pkey'),
)


async def init_pg(app):
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
        loop=app.loop)
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

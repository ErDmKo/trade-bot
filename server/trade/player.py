import asyncio
import json
from server import db
from server import utils 
from ..btcelib import TradeAPIv1, PublicAPIv3
from .SimpleStrategy import SimpleStrategy
from .ThreadStrategy import ThreadStrategy

async def load_strategy(app):
    while True:
        engine = app.get('db')
        if not engine:
            await asyncio.sleep(0.1)
            continue

        async with engine.acquire() as conn:
            tradeApi = app['privapi']
            pubApi = PublicAPIv3('btc_usd')
            app['strategy'] = await ThreadStrategy.create(conn, tradeApi, pubApi)
        break

async def on_shutdown(app):
    app['strategy_maker'].cancel()

def add_simple(app):
    app['strategy_maker'] = asyncio.ensure_future(
        load_strategy(app),
        loop=app.loop
    )
    app.on_shutdown.append(on_shutdown)

async def main_test(loop):
    conf = utils.load_config()
    engine = await db.get_engine(conf['postgres'], loop)
    async with engine.acquire() as conn:
        tradeApi = TradeAPIv1({
            'Key': conf['api']['API_KEY'],
            'Secret': conf['api']['API_SECRET']
            })
        pubApi = PublicAPIv3('btc_usd')
        player = await ThreadStrategy.create(conn, tradeApi, pubApi, True)
        # player = await SimpleStrategy.create(conn, tradeApi, pubApi, True)
        clear_order = await conn.execute(db.demo_order.delete())
        cursor = await conn.execute(
                db.history
                    .select()
                    .where(db.history.c.pair == player.PAIR)
                    .order_by(db.history.c.pub_date)
                    .offset(player.OFFSET)
                    .limit(player.LIMIT)
                )
        async for tick in cursor:
            await player.tick(json.loads(tick.resp))

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

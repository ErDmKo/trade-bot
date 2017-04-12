import asyncio
import json
import sys
from decimal import Decimal as D
from server import db
from server import utils 
from ..btcelib import TradeAPIv1, PublicAPIv3
from .SimpleStrategy import SimpleStrategy
from .ThreadStrategy import ThreadStrategy

async def load_strategy(app, strategy_name):
    while True:
        engine = app.get('db')
        if not engine:
            await asyncio.sleep(0.1)
            continue

        async with engine.acquire() as conn:
            tradeApi = app['privapi']
            pubApi = PublicAPIv3('btc_usd')
            module = __import__('server.trade.{}'.format(
                strategy_name
            ), fromlist=[strategy_name])
            print(strategy_name)
            app['strategy'] = await getattr(module, strategy_name).create(
                conn,
                tradeApi,
                pubApi,
                False,
                app['socket_channels']['log']
            )
        break

async def on_shutdown(app):
    app['strategy_maker'].cancel()

def add_strategy(app, strategy_name='ThreadStrategy'):
    app['strategy_maker'] = asyncio.ensure_future(
        load_strategy(app, strategy_name),
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

        if len(sys.argv) > 2:
            strategy_name = sys.argv[2]
            module = __import__('server.trade.{}'.format(
                strategy_name
            ), fromlist=[strategy_name])
            strategy = getattr(module, strategy_name)
        else:
            strategy = ThreadStrategy

        player = await strategy.create(conn, tradeApi, pubApi, True)
        clear_order = await conn.execute(db.demo_order.delete())
        print('player')
        cursor = await conn.execute(
                db.history
                    .select()
                    .where(
                        (db.history.c.pair == player.PAIR)
                        & db.history.c.pub_date.between('2017-03-22 14:36:00', '2017-03-25 14:39:00')
                    )
                    .order_by(db.history.c.pub_date)
                    .offset(player.OFFSET)
                    .limit(player.LIMIT)
                )
        async for tick in cursor:
            await player.tick(json.loads(tick.resp), {'funds': {
                'usd': D(1000),
                'btc': D(1)
            }})

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

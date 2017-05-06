import asyncio
import json
import sys
from decimal import Decimal as D

import sqlalchemy as sa

from server import db
from server import utils 
from ..btcelib import TradeAPIv1, PublicAPIv3
from .SimpleStrategy import SimpleStrategy
from .ThreadStrategy import ThreadStrategy

START_TIME = '2017-04-16 00:00'
END_TIME = '2017-05-08 23:59'

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

        strategy_name = 'ThreadStrategy'

        if len(sys.argv) > 2:
            strategy_name = sys.argv[2]

        module = __import__('server.trade.{}'.format(
            strategy_name
        ), fromlist=[strategy_name])
        strategy = getattr(module, strategy_name)

        player = await strategy.create(conn, tradeApi, pubApi, True)
        clear_order = await conn.execute(db.demo_order.delete())
        print('player {}'.format(strategy_name))
        cursor = await conn.execute(
                db.history
                    .select()
                    .where(
                        (db.history.c.pair == player.PAIR)
                        & (sa.sql.func.random() < 0.005)
                        & db.history.c.pub_date.between(START_TIME, END_TIME)
                    )
                    .order_by(db.history.c.pub_date)
                    .offset(player.OFFSET)
                    .limit(player.LIMIT)
                )
        index = 0
        async for tick in cursor:
            balance = getattr(player, 'balance', {
                'usd': D(3),
                'btc': D(0.3)
            })
            depth = json.loads(tick.resp)
            depth['pub_date'] = tick.pub_date
            await player.tick(depth, {
                'funds': balance
            })
            index += 1

        print(balance, index)

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

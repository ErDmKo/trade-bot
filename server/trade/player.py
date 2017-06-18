import asyncio
import json
import sys
from decimal import Decimal as D

import sqlalchemy as sa

from server import db
from server import utils 
from ..btcelib import TradeAPIv1, PublicAPIv3
from .MultiplePairs import MultiplePairs

START_TIME = '2017-06-16 00:00'
END_TIME = '2017-06-18 23:59'

async def load_strategy(app, strategy_name):
    while True:
        engine = app.get('db')
        if not engine:
            await asyncio.sleep(0.1)
            continue

        async with engine.acquire() as conn:
            tradeApi = app['privapi']
            pubApi = PublicAPIv3(*MultiplePairs.PAIRS)
            module = __import__('server.trade.{}'.format(
                strategy_name
            ), fromlist=[strategy_name])
            print(strategy_name)
            app['strategy'] = await MultiplePairs.create(
                conn,
                tradeApi,
                pubApi,
                pair_list = MultiplePairs.PAIRS,
                strategy = getattr(module, strategy_name),
                is_demo = False,
                log = app['socket_channels']['log']
            )
        break

async def on_shutdown(app):
    app['strategy_maker'].cancel()

def add_strategy(app, strategy_name='VolumeStrategy'):
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
        pubApi = PublicAPIv3(*MultiplePairs.PAIRS)

        strategy_name = 'MultiplePairs'

        if len(sys.argv) > 2:
            strategy_name = sys.argv[2]

        module = __import__('server.trade.{}'.format(
            strategy_name
        ), fromlist=[strategy_name])
        strategy = getattr(module, strategy_name)

        player = await strategy.create(
            conn,
            tradeApi,
            pubApi,
            is_demo = True,
            pair_list = MultiplePairs.PAIRS
        )
        clear_order = await conn.execute(db.demo_order.delete())
        print('player {}'.format(strategy_name))
        cursor = await conn.execute(
                db.history
                    .select()
                    .where(
                        #(sa.sql.func.random() < 0.1) &
                        db.history.c.pub_date.between(START_TIME, END_TIME)
                    )
                    .order_by(db.history.c.pub_date)
                    .offset(player.OFFSET)
                    .limit(player.LIMIT)
                )
        index = 0
        async for tick in cursor:
            balance = getattr(player, 'balance', {
                'usd': D(100),
                'btc': D(0.08),
                'rur': D(0),
                'eth': D(0)
            })
            depth = json.loads(tick.resp)
            depth['pub_date'] = tick.pub_date
            await player.tick(depth, tick.pair, {
                'funds': balance
            })
            index += 1

        print(balance, index)

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

import asyncio
import json
import sys
import logging
from decimal import Decimal as D
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import sqlalchemy as sa

from server import db
from server import utils 
from ..btcelib import TradeAPIv1, PublicAPIv3
from .MultiplePairs import MultiplePairs

START_TIME = '2017-10-10 00:00'
END_TIME = '2017-10-22 23:59'

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
            logger.info(strategy_name)
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

async def main_test(loop, strategy_name='MultiplePairs'):
    conf = utils.load_config()
    engine = await db.get_engine(conf['postgres'], loop)
    async with engine.acquire() as conn:
        tradeApi = TradeAPIv1({
            'Key': conf['api']['API_KEY'],
            'Secret': conf['api']['API_SECRET']
        })
        pubApi = PublicAPIv3(*MultiplePairs.PAIRS)

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
        logger.info('player {} {}'.format(strategy_name, ", ".join(player.PAIRS)))
        cursor = await conn.execute(
            db.history
            .select()
            .where(
                (sa.sql.func.random() < 0.01) &
                db.history.c.pair.in_(player.PAIRS) &
                db.history.c.pub_date.between(START_TIME, END_TIME)
                )
            .order_by(db.history.c.pub_date)
            .offset(player.OFFSET)
            .limit(player.LIMIT)
            )
        index = 0
        async for tick in cursor:
            balance = getattr(player, 'balance', {
                'usd': D(1000),
                'btc': D(0),
                'rur': D(0),
                'eth': D(20)
            })
            depth = json.loads(tick.resp)
            depth['pub_date'] = tick.pub_date
            await player.tick(depth, tick.pair, {
                'funds': balance
            })
            index += 1

        logger.info(' - '.join([str(balance), str(index)]))

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

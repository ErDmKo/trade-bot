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

START_TIME = '2018-02-08 00:00'
END_TIME = '2018-02-08 23:59'

async def load_strategy(app, strategy_name):
    while True:
        engine = app.get('db')
        if not engine:
            await asyncio.sleep(0.1)
            continue

        tradeApi = app['privapi']
        pubApi = PublicAPIv3(*MultiplePairs.PAIRS)
        module = __import__('server.trade.{}'.format(
            strategy_name
        ), fromlist=[strategy_name])
        logger.info(strategy_name)

        app['strategy'] = await MultiplePairs.create(
            engine,
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

def get_query(player, start_date, end_date):
    start_date = start_date or START_TIME
    end_date = end_date or END_TIME
    logger.info('Period form {} to {}'.format(start_date, end_date))
    return (
        db.history
        .select()
        .where(
            (sa.sql.func.random() < 0.05) &
            db.history.c.pair.in_(player.PAIRS) &
            db.history.c.pub_date.between(start_date, end_date)
        )
        .order_by(db.history.c.pub_date)
        .offset(player.OFFSET)
        .limit(player.LIMIT)
    )

async def main_test(
        loop,
        strategy_name='',
        strategy_class=None,
        start_date=None,
        end_date=None,
        conf=None,
        constructor={}
    ):
    conf = conf or utils.load_config()
    engine = await db.get_engine(conf['postgres'], loop)
    async with engine.acquire() as conn:
        tradeApi = TradeAPIv1({
            'Key': conf['api']['API_KEY'],
            'Secret': conf['api']['API_SECRET']
        })
        pubApi = PublicAPIv3(*MultiplePairs.PAIRS)

        if len(sys.argv) > 2:
            strategy_name = sys.argv[2]

        if strategy_class:
            strategy = strategy_class
        else:
            module = __import__('server.trade.{}'.format(
                strategy_name
            ), fromlist=[strategy_name])
            strategy = getattr(module, strategy_name)
        constructor.update({
            'is_demo': True,
            'pair_list': MultiplePairs.PAIRS
        }) 
        player = await strategy.create(
            engine,
            tradeApi,
            pubApi,
            **constructor
        )
        clear_order = await conn.execute(db.demo_order.delete())
        logger.info('player {} {}'.format(strategy_name, ", ".join(player.PAIRS)))
        query = get_query(player, start_date, end_date)
        cursor = await conn.execute(query)
        index = 0
        balance = 'Nothing has founded' 
        async for tick in cursor:
            balance = getattr(player, 'balance', {
                'usd': D(2000),
                'btc': D(0),
                'rur': D(0),
                'eth': D(100)
            })
            depth = json.loads(tick.resp)
            depth['pub_date'] = tick.pub_date
            await player.tick(depth, tick.pair, {
                'funds': balance
            })
            index += 1

        logger.info(' - '.join([str(balance), str(index)]))

def run_script(
        strategy_name='MultiplePairs',
        strategy_class = None,
        start_date=START_TIME,
        end_date=END_TIME,
        conf = None,
        constructor = {}
    ):
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(
           loop, 
           strategy_name,
           strategy_class,
           start_date,
           end_date,
           conf,
           constructor
       )
   )

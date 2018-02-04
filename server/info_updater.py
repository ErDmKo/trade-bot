import asyncio
import aiohttp
import json
import logging
import datetime
from .utils import dumps
from .db import history
import sys, traceback

logger = logging.getLogger(__name__)

def print_exception():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_tb(exc_traceback)
    traceback.print_exception(exc_type, exc_value, exc_traceback)

async def update_info(app):

    while True:
        try:
            pair_info = await app['pubapi'].call('ticker')
            depth_info = await app['pubapi'].call('depth', limit=50)
            balans_info = await app['privapi'].call('getInfo')
        except Exception as e:
            print_exception()
            continue

        channels = app['socket_channels']
        logger.info('tik - {}'.format(datetime.datetime.now().isoformat()))

        if app.get('strategy'):
            strategy = app.get('strategy')
            for pair, info in depth_info.items():
                try:
                    await app['strategy'].tick(info, pair, balans_info)
                except Exception as e:
                    print('Error')
                    print_exception()

        await channels['balance_socket'].broadcast(balans_info)
        await channels['depth_socket'].broadcast(depth_info)
        await channels['pair_socket'].broadcast(pair_info)

        if app.get('db'):
            async with app['db'].acquire() as conn:
                await conn.execute(history.delete().where(
                    history.c.pub_date < 
                        datetime.datetime.now() - datetime.timedelta(days=90)
                ))
                for pair, info in depth_info.items():
                    result = await conn.execute(
                        history.insert().values(
                            pair = pair,
                            resp = dumps(info)
                        )
                    )
        await asyncio.sleep(1)
    
async def on_shutdown(app):
    app['updater_future'].cancel()
    
def setup_info_updater(app):
    app['updater_future'] = asyncio.ensure_future(
        update_info(app),
        loop=app.loop
    )
    app.on_shutdown.append(on_shutdown)

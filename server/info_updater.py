import asyncio
import aiohttp
import json
import datetime
from .utils import dumps
from .db import history
import sys, traceback

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
        print('tik - {}'.format(datetime.datetime.now().isoformat()))

        if app.get('strategy'):
            strategy = app.get('strategy')
            for pair, info in depth_info.items():
                if strategy.PAIR == pair:
                    try:
                        await app['strategy'].tick(info, balans_info)
                    except Exception as e:
                        print('Error')
                        print_exception()


        channels['balance_socket'].broadcast(balans_info)
        channels['depth_socket'].broadcast(depth_info)
        channels['pair_socket'].broadcast(pair_info)

        if app.get('db'):
            async with app['db'].acquire() as conn:
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

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

        print('tik - {}'.format(datetime.datetime.now().isoformat()))

        if app.get('balance_socket'):
            ws = app.get('balance_socket')

            try:
                ws.send_json(balans_info, dumps = dumps)
            except RuntimeError as e:
                if str(e) == 'websocket connection is closing':
                    print('close client')
                else:
                    print('client ERROR')
                    raise e

        if app.get('depth_socket'):
            ws = app.get('depth_socket')
            try:
                ws.send_json(depth_info, dumps = dumps)
            except RuntimeError as e:
                if str(e) == 'websocket connection is closing':
                    print('close client')
                else:
                    print('client ERROR')
                    raise e

        if app.get('pair_socket'):
            ws = app.get('pair_socket')
            try:
                ws.send_json(pair_info, dumps = dumps)
            except RuntimeError as e:
                if str(e) == 'websocket connection is closing':
                    print('close client')
                else:
                    print('client ERROR')
                    raise e

    
        if app.get('db'):
            async with app['db'].acquire() as conn:
                for pair, info in depth_info.items():
                    result = await conn.execute(
                        history.insert().values(
                            pair = pair,
                            resp = dumps(info)
                        )
                    )
        if app.get('strategy'):
            strategy = app.get('strategy')
            for pair, info in depth_info.items():
                if strategy.PAIR == pair:
                    try:
                        await app['strategy'].tick(info)
                    except Exception as e:
                        print('Error')
                        print_exception()
        await asyncio.sleep(2)
    
async def on_shutdown(app):
    app['updater_future'].cancel()
    
def setup_info_updater(app):
    app['updater_future'] = asyncio.ensure_future(
        update_info(app),
        loop=app.loop
    )
    app.on_shutdown.append(on_shutdown)

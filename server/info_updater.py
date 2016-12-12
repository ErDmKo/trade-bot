import asyncio
import aiohttp
import json
from .utils import dumps

async def update_info(app):

    while True:
        pair_info = await app['pubapi'].call('ticker')
        depth_info = await app['pubapi'].call('depth')
        print('tik')

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
        await asyncio.sleep(2)
    
async def on_shutdown(app):
    app['updater_future'].cancel()

    
def setup_info_updater(app):
    app['updater_future'] = asyncio.ensure_future(
        update_info(app),
        loop=app.loop
    )
    app.on_shutdown.append(on_shutdown)

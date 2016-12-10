import asyncio
import json
from .utils import dumps

async def update_info(app):

    while True:
        info = await app['pubapi'].call('ticker')
        print('tik')
        if app.get('pair_socket'):
            ws = app.get('pair_socket')
            ws.send_json(info, dumps = dumps)
        await asyncio.sleep(3)
    
async def on_shutdown(app):
    app['updater_future'].cancel()

    
def setup_info_updater(app):
    app['updater_future'] = asyncio.ensure_future(
        update_info(app),
        loop=app.loop
    )
    app.on_shutdown.append(on_shutdown)

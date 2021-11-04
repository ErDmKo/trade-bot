import asyncio
import logging
import pathlib
from server.tinkoff import getAsyncClient
import sys

import jinja2

import aiohttp_jinja2
from aiohttp import web
import os
from .routes import setup_routes
from .utils import load_config, BList
from collections import defaultdict
from .info_updater import setup_info_updater
from .middlewares import setup_middlewares
from .db import close_pg, init_pg
from .trade.player import add_strategy
from .trade.MultiplePairs import MultiplePairs

from server import btcelib

logger = logging.getLogger(__name__)


def init():
    logger.info('[{}] App init'.format(os.getpid()))
    # setup application and extensions
    app = web.Application()

    # load config from yaml file in current dir
    conf = load_config(str(pathlib.Path('.') / 'config' / 'base.yaml'))
    app['config'] = conf

    # app['pubapi'] = btcelib.PublicAPIv3(*MultiplePairs.PAIRS)
    app['socket_channels'] = defaultdict(BList)

    # setup Jinja2 template renderer
    aiohttp_jinja2.setup(
        app, loader=jinja2.PackageLoader('server', 'templates'))

    # add strategy
    # create connection to the database
    app.on_startup.append(init_pg)
    # shutdown db connection on exit
    app.on_cleanup.append(close_pg)
    # setup views and routes
    setup_routes(app)
    setup_middlewares(app)
    # setup_info_updater(app)
    # prog = sys.argv[1] if len(sys.argv) > 1 else ''
    # add_strategy(app, prog if prog else 'VolumeStrategy')

    return app


async def asyncInit(app):
    runner = web.AppRunner(app)
    if app['config'].get('pubtoken'):
        app['brokerClient'] = await getAsyncClient(app['config'].get('pubtoken'))
    await runner.setup()
    site = web.TCPSite(
        runner,
        app['config']['host'],
        app['config']['port']
    )
    logger.info(' Serve at {}:{}'.format(
        app['config']['host'],
        app['config']['port']
    ))
    await site.start()
    while True:
        await asyncio.sleep(3600)
    # wait for finish signal
    # logger.info(' after clean')
    # await runner.cleanup()


def main():
    # init logging
    logging.basicConfig(level=logging.DEBUG)

    app = init()
    if not app:
        return
    logger.debug('app inited')
    asyncio.run(asyncInit(app))


if __name__ == '__main__':
    main()

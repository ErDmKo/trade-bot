import asyncio
import logging
import pathlib

import jinja2

import aiohttp_jinja2
from aiohttp import web
from .routes import setup_routes
from .utils import load_config, BList, SharedKeyDict
from .info_updater import setup_info_updater
from .middlewares import setup_middlewares
from .db import close_pg, init_pg
from .trade.player import add_simple

from server import btcelib 


def init():
    loop = asyncio.get_event_loop()

    # setup application and extensions
    app = web.Application(loop=loop)

    # load config from yaml file in current dir
    conf = load_config(str(pathlib.Path('.') / 'config' / 'base.yaml'))
    app['config'] = conf

    app['pubapi'] = btcelib.PublicAPIv3('btc_usd', 'btc_rur')
    app['privapi'] = btcelib.TradeAPIv1({
        'Key': conf['api']['API_KEY'],
        'Secret': conf['api']['API_SECRET']
    })
    app['socket_channels'] = SharedKeyDict(lambda key: BList(app, key))

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
    setup_info_updater(app)
    add_simple(app)

    return app

def main():
    # init logging
    logging.basicConfig(level=logging.DEBUG)

    app = init()
    web.run_app(
        app,
        host=app['config']['host'],
        port=app['config']['port']
    )

if __name__ == '__main__':
    main()

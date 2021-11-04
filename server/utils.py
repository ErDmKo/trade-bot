import json
import os
import yaml
import pathlib
import aiohttp
from decimal import Decimal
from datetime import date as dateFormat
import logging

logger = logging.getLogger(__name__)

class BList(list):

    async def broadcast(self, message):
        for waiter in self:
            exception = waiter.exception()
            if exception:
                print(
                    'close because socker error {}'
                    .format(exception)
                )
                self.remove(waiter)
                continue
            try:
                await waiter.send_json(message, dumps=dumps)
            except RuntimeError as e:
                if str(e) == 'websocket connection is closing':
                    print('close by client')
                    self.remove(waiter)
                else:
                    print('close by socker error')
                    self.remove(waiter)
                    raise e


async def handle_socket(ws, app=False, method=False):
    api = app.get('brokerClient')
    logger.info('handle call')
    async for msg in ws:
        logger.info(f'new message {msg} {aiohttp.WSMsgType.TEXT} {msg.type == aiohttp.WSMsgType.TEXT}')
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data.replace('"', '') == 'connect':
                logger.info(f'connect - "{api}"')
                if api:
                    info = await api.call(method)
                    await ws.send_json(info, dumps=dumps)
            elif msg.data == 'close':
                await ws.close()
            else:
                logger.info(f'unknown message data - "{msg.data}"')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.info(f'ws connection closed with exception {ws.exception()}')
    return ws


def load_config(fname=str(pathlib.Path('.') / 'config' / 'base.yaml')):
    with open(fname, 'rt') as f:
        data = yaml.load(f, Loader=yaml.BaseLoader)
    localConf = os.path.abspath(os.path.join(fname, '..', 'local.yaml'))
    if os.path.isfile(localConf):
        logger.info('Use local config')
        with open(localConf) as f:
            data.update(yaml.load(f, Loader=yaml.BaseLoader))
    return data


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, dateFormat):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)


def dumps(data):
    return json.dumps(data, cls=DecimalEncoder)


def loads(data):
    return json.loads(data)

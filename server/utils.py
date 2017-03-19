import json
import yaml
import pathlib
import aiohttp
from collections import defaultdict
from decimal import Decimal
from datetime import date as dateFormat

class SharedKeyDict(defaultdict):

    def __missing__(self, key):
        if self.default_factory:
            dict.__setitem__(self, key, self.default_factory(key))
            return self[key]
        else:
            super().__missing__(key)

class BList(list):

    def __init__(self, app, key, *ar, **kw):
        super().__init__(*ar, **kw)
        self.app = app
        self.key = key

    def broadcast(self, message):
        for waiter in self:
            try:
                waiter.send_json(message, dumps=dumps)
            except RuntimeError as e:
                if str(e) == 'websocket connection is closing':
                    print('close client')
                    self.app['socket_channels'][self.key].remove(waiter)
                else:
                    print('client ERROR')
                    raise e

async def handle_socket(ws, api, method):

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'connect':
                info = await api.call(method)
                ws.send_json(info, dumps = dumps)
            elif msg.data == 'close':
                await ws.close()
            else:
                print(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())
    return ws

def load_config(fname=str(pathlib.Path('.') / 'config' / 'base.yaml')):
    with open(fname, 'rt') as f:
        data = yaml.load(f)

    with open(str(pathlib.Path('.') / 'config' / 'local.yaml'), 'rt') as f:
        data.update(yaml.load(f))
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

import json
import yaml
import pathlib
import aiohttp
from decimal import Decimal
from datetime import date as dateFormat

class BList(list):

    def broadcast(self, message):
        for waiter in self:
            try:
                waiter.send_json(message, dumps=dumps)
            except RuntimeError as e:
                if str(e) == 'websocket connection is closing':
                    print('close client')
                    self.remove(waiter)
                else:
                    print('client ERROR')
                    raise e

async def handle_socket(ws, api=False, method=False):

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'connect':
                if api:
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

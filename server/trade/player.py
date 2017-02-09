import asyncio
from ..db import get_engine, history, add_order
from ..utils import load_config
from ..btcelib import TradeAPIv1

class Player(object):

    @classmethod
    async def create(cls, connection, api):
        self = Player()
        self.api = api
        self.connection = connection
        await self.get_balance('usd')
        return self

    async def get_balance(self, currency='btc'):
        balnce_info = await self.api.call('getInfo')
        self.balance = balnce_info['funds']
        return self.balance[currency]

    async def sel(self):
        await self.get_balance()

    async def buy(self):
        await self.get_balance()

    async def tick(self, resp):
        for currency, amount in self.balance.items():
            if amount > 0:
                pass

async def main_test(loop):
    conf = load_config()
    engine = await get_engine(conf['postgres'], loop)
    async with engine.acquire() as conn:
        api = TradeAPIv1({
            'Key': conf['api']['API_KEY'],
            'Secret': conf['api']['API_SECRET']
            })
        player = await Player.create(conn, api)
        cursor = await conn.execute(history.select().where(history.c.pair == 'btc_usd').limit(10))
        async for tick in cursor:
            await player.tick(tick)

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

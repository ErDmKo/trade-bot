import sqlalchemy as sa
import asyncio
import json
from decimal import Decimal as D
from server import db
from ..utils import load_config
from ..btcelib import TradeAPIv1, PublicAPIv3

class Player(object):

    LIMIT = 10000
    PAIR = 'btc_usd'
    FEE = 0.1

    @classmethod
    async def create(cls, connection, tradeApi, pubApi):
        self = Player()
        self.api = tradeApi
        self.pubApi = pubApi
        self.connection = connection
        self.prec = D(10) ** -3
        currency = self.PAIR.split('_')
        self.currency = {
            'buy': currency[1],
            'sell': currency[0]
        }
        await self.get_pair_info()
        await self.get_order()
        await self.get_balance()
        return self

    async def get_pair_info(self):
         resp = await self.pubApi.call('info')
         self.pair_info = resp['pairs'][self.PAIR]
         self.prec = D(10) ** -self.pair_info['decimal_places']
         return self.pair_info

    async def get_order(self):
        cursor = await self.connection.execute(
            db.order.select().order_by(sa.desc(db.order.c.pub_date)).limit(1)
        )
        async for order in cursor:
            self.order = order
            return order
        self.order = None
        return None

    async def get_balance(self, currency='btc'):
        balnce_info = await self.api.call('getInfo')
        self.balance = balnce_info['funds']
        return self.balance[currency]

    def get_new_amount(self, currency):
        return max([
            self.pair_info['min_amount'],
            D(self.balance[currency]/1000).quantize(self.prec)
        ])


    async def sell(self, depth):
        amount = self.get_new_amount(self.currency['sell'])
        price = depth['asks'][0][0]
        info = dict(
            conn = self.connection,
            price = price,
            pair = self.PAIR,
            amount = amount,
            is_sell = True
        )
        order = await db.add_order(**info)

        if self.order:
            print('sell before {} now {}'.format(self.order.price, info['price']))

    async def buy(self, depth):
        await self.get_balance()
        amount = self.get_new_amount(self.currency['buy'])
        price = depth['bids'][0][0]
        info = dict(
            conn = self.connection,
            price = price,
            pair = self.PAIR,
            amount = amount,
            is_sell = False
        )
        order = await db.add_order(**info)
        print('buy before {} now {}'.format(self.order.price, info['price']))

    def get_best_price(self, deps):
        fee = float(self.pair_info['fee']) + self.FEE
        all_money = self.order.amount * self.order.price
        fee_money = all_money * fee
        if self.order.is_sell:
            return float(deps['bids'][0][0]) - fee_money
        else:
            return float(deps['asks'][0][0]) + fee_money

    async def tick(self, resp):
        self.depth = resp
        order = await self.get_order()
        if not order:
            print ('init')
            for currency, amount in self.balance.items():
                if amount > 0:
                    await self.sell(resp)
        else:
            best_price = self.get_best_price(resp)
            if order.is_sell:
                if order.price < best_price:
                    await self.buy(resp)
            else:
                if order.price > best_price:
                    await self.sell(resp)

async def main_test(loop):
    conf = load_config()
    engine = await db.get_engine(conf['postgres'], loop)
    async with engine.acquire() as conn:
        tradeApi = TradeAPIv1({
            'Key': conf['api']['API_KEY'],
            'Secret': conf['api']['API_SECRET']
            })
        pubApi = PublicAPIv3('btc_usd')
        player = await Player.create(conn, tradeApi, pubApi)
        cursor = await conn.execute(
                db.history.select().where(db.history.c.pair == player.PAIR).limit(player.LIMIT))
        async for tick in cursor:
            await player.tick(json.loads(tick.resp))

def run_script():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main_test(loop))

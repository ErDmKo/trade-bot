import sqlalchemy as sa
from decimal import Decimal as D
from server import db
from server import utils 

class SimpleStrategy(object):

    LIMIT = 10000
    PAIR = 'btc_usd'
    FEE = 0.1

    @classmethod
    async def create(cls, connection, tradeApi, pubApi):
        self = SimpleStrategy()
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
            db.order.select()
                .where(db.order.c.pair == self.PAIR)
                .order_by(sa.desc(db.order.c.pub_date)).limit(1)
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


    def get_order_info(self, price, amount, is_sell):
        return dict(
            conn = self.connection,
            pair = self.PAIR,
            price = price,
            amount = amount,
            is_sell = is_sell
        )

    async def sell(self, depth):
        amount = self.get_new_amount(self.currency['sell'])
        price = depth['bids'][0][0]
        info = self.get_order_info(price, amount, True)
        print(info)
        api_resp = await self.api.call(
            'Trade',
            pair=self.PAIR,
            type='sell',
            rate=price,
            amount = amount
        )
        self.balance = api_resp['funds']
        info['api'] = utils.dumps(api_resp)
        order = await db.add_order(**info)

        if self.order:
            print('sell before {} now {}'.format(self.order.price, info['price']))

    async def buy(self, depth):
        amount = self.get_new_amount(self.currency['buy'])
        price = depth['asks'][0][0]
        info = self.get_order_info(price, amount, False)
        print(info)
        api_resp = await self.api.call(
            'Trade',
            pair=self.PAIR,
            type='buy',
            rate=price,
            amount = amount
        )
        self.balance = api_resp['funds']
        info['api'] = utils.dumps(api_resp)
        order = await db.add_order(**info)

        print('buy before {} now {}'.format(self.order.price, info['price']))

    def get_best_price(self, amount, price, diretion):
        fee = (float(self.pair_info['fee']) + self.FEE) / 100
        all_money = amount * float(price)
        dellta = -1 if diretion else 1
        out = all_money * (1 + dellta * fee)
        # print('{} * {} * (1 {} * {}) '.format(amount, price, dellta, fee))
        return out


    async def tick(self, resp):
        self.depth = resp
        order = await self.get_order()
        if not order:
            print ('init')
            for currency, amount in self.balance.items():
                if amount > 0:
                    await self.sell(resp)
        else:
            old_money = self.get_best_price(self.order.amount, self.order.price, True)
            if order.is_sell:
                best_price = self.get_best_price(self.order.amount, resp['asks'][0][0], False)
                print('buy', old_money, resp['asks'][0][0], best_price) 
                if old_money > best_price:
                    await self.buy(resp)
            else:
                best_price = self.get_best_price(self.order.amount, resp['bids'][0][0], False)
                print('sell', old_money, resp['asks'][0][0], best_price) 
                if old_money < best_price:
                    await self.sell(resp)

import sqlalchemy as sa
from decimal import Decimal as D
from server import db
from server import utils 

class SimpleStrategy(object):

    OFFSET = 0
    LIMIT = 10000
    PAIR = 'btc_usd'
    FEE = 0.1

    def __init__(self, log):
        self.log = log

    @classmethod
    def init_self(cls, log):
        return SimpleStrategy(log)

    @classmethod
    async def create(cls, connection, tradeApi, pubApi, is_demo=False, log=False):
        self = cls.init_self(log)
        self.is_demo = is_demo
        self.api = tradeApi
        self.pubApi = pubApi
        self.connection = connection
        self.prec = D(10) ** -3
        currency = self.PAIR.split('_')
        self.currency = {
            'buy': currency[1],
            'sell': currency[0]
        }
        self.directions = {
            currency[1]: 'buy',
            currency[0]: 'sell' 
        }
        self.order_table = 'demo_order' if is_demo else 'order'
        await self.get_pair_info()
        await self.get_order()
        await self.get_balance()
        return self

    def print(self, string):
        print(string)
        if self.log:
            self.log.broadcast({
                'message': string
            })

    def get_order_table(self):
        return getattr(db, self.order_table)

    async def get_pair_info(self):
         resp = await self.pubApi.call('info')
         self.pair_info = resp['pairs'][self.PAIR]
         self.prec = D(10) ** -self.pair_info['decimal_places']
         return self.pair_info

    async def add_order(self, info):
        result = await self.connection.execute(
            self.get_order_table().insert().values(**info)
        )
        result_info = await result.first()
        return result_info

    async def get_order(self):
        order = self.get_order_table()
        cursor = await self.connection.execute(
            order.select()
                .where(order.c.pair == self.PAIR)
                .order_by(sa.desc(order.c.pub_date)).limit(1)
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
        return float(max([
            self.pair_info['min_amount'],
            D(self.balance[self.currency['sell']]/1000).quantize(self.prec)
        ]))


    def get_order_info(self, price, amount, is_sell):
        return dict(
            pair = self.PAIR,
            price = price,
            amount = amount,
            is_sell = is_sell,
            extra = {}
        )

    async def trade(self, direction, price, amount):
        if self.is_demo:
            return {
                "demo_order": "1",
                "funds": self.balance
            }
        api_resp = await self.api.call(
            'Trade',
            pair=self.PAIR,
            type=direction,
            rate=price,
            amount = amount
        )
        self.balance = api_resp['funds']
        return api_resp

    def print_order(self, info, direction, old_order):
        if old_order:
            self.print('{} before {} now {}'.format(
                direction,
                old_order.price,
                info['price'],
                )
            )
        else:
            self.print('{} before init now {}'.format(
                direction,
                info['price'])
            )

    async def sell(self, depth, old_order=False):
        currency = self.currency['sell']
        amount = self.get_new_amount(currency)
        price = depth['bids'][0][0]
        if self.balance[currency] < amount:
            self.print('Low balance {} {} need more {} '.format(
                self.balance[currency],
                currency,
                amount
                )
            )
            return
        info = self.get_order_info(price, amount, True)
        api_resp = await self.trade('sell', price, amount)
        info['api'] = utils.dumps(api_resp)
        order = await self.add_order(info)

        self.print_order(info, 'sell', old_order)

        return order


    async def buy(self, depth, old_order=False):
        currency = self.currency['buy']
        amount = self.get_new_amount(currency)
        price = depth['asks'][0][0]
        info = self.get_order_info(price, amount, False)
        if self.balance[currency] < float(price) * amount:
            self.print('Low balance {} {} need more {} '.format(
                self.balance[currency],
                currency,
                (float(price) * amount) - float(self.balance[currency])
                )
            )
            return
        api_resp = await self.trade('buy', price, amount);
        info['api'] = utils.dumps(api_resp)
        order = await self.add_order(info)

        self.print_order(info, 'buy', old_order)

        return order

    def get_best_price(self, amount, price, diretion):
        fee = (float(self.pair_info['fee']) + self.FEE) / 100
        all_money = amount * float(price)
        dellta = -1 if diretion else 1
        out = all_money * (1 + dellta * fee)
        # self.print('{} * {} * (1 {} * {}) '.format(amount, price, dellta, fee))
        return out

    def get_stat(self):
        return self.order

    async def tick(self, resp, balance=False):
        self.depth = resp
        if not balance:
            await self.get_balance()
        order = await self.get_order()
        if not order:
            self.print('init order is {}'.format(order))
            for currency, amount in self.balance.items():
                if amount > 0:
                    await self.sell(resp)
                    return
        else:
            old_money = self.get_best_price(self.order.amount, self.order.price, True)
            if order.is_sell:
                best_price = self.get_best_price(self.order.amount, resp['asks'][0][0], False)
                if not self.is_demo:
                    self.print('buy', old_money, resp['asks'][0][0], best_price) 
                if old_money > best_price:
                    await self.buy(resp, self.order)
            else:
                best_price = self.get_best_price(self.order.amount, resp['bids'][0][0], True)
                if not self.is_demo:
                    self.print('sell', old_money, resp['bids'][0][0], best_price) 
                if old_money < best_price:
                    await self.sell(resp, self.order)

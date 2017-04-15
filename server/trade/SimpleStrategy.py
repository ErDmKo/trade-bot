import json
import sqlalchemy as sa
from decimal import Decimal as D
from server import db
from server import utils 

class SimpleStrategy(object):

    OFFSET = 0
    LIMIT = 10000
    PAIR = 'btc_usd'
    FEE = 0.1

    @classmethod
    def init_self(cls):
        return cls()

    @classmethod
    async def create(cls, connection, tradeApi, pubApi, is_demo=False, log=False):
        self = cls.init_self()
        self.is_demo = is_demo
        self.log = log
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
        if not info['api']:
            raise Exception('WTF dude?!?!')

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

    def get_new_amount(self, currency, amount, volume):
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

    async def trade(self, direction, info):
        if self.is_demo:
            return {
                "demo_order": "1",
                "funds": self.balance
            }
        api_resp = await self.api.call(
            'Trade',
            pair=info['pair'],
            type=direction,
            rate=info['price'],
            amount = info['amount']
        )
        if float(api_resp['received']) < info['amount']:
            self.print('CancelOrder {}'.format(
                api_resp['order_id']
            ))
            try:
                result = await self.api.call(
                    'CancelOrder',
                    order_id=api_resp['order_id']
                )
                self.balance = result['funds']
                return False
            except Exception as e:
                self.print('Fail to cancel order! {}'.format(e))
        currency = self.currency[direction]
        api_resp['old_balance'] = self.balance.copy()
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

    def get_trade_info(self, depth, direction, amount=False):
        is_sell = direction == 'sell'
        currency = self.currency[direction]
        price, volume = depth['bids' if is_sell else 'asks'][0]
        info_amount = self.get_new_amount(currency, amount, volume)
        money = info_amount if is_sell else float(price) * info_amount
        if self.balance[currency] < money:
            self.print('Low balance {} {} need more {} '.format(
                self.balance[currency],
                currency,
                (money - float(self.balance[currency]))
                )
            )
            return 
        info = self.get_order_info(price, info_amount, is_sell)
        return info
        
    async def sell(self, depth, old_order=False, amount=False):
        info = self.get_trade_info(depth, 'sell', amount)
        if not info:
            return False
        api_resp = await self.trade('sell', info)
        if not api_resp:
            return False
        info['api'] = json.loads(utils.dumps(api_resp))
        order = await self.add_order(info)

        self.print_order(info, 'sell', old_order)
        info['id'] = order.id
        return info


    async def buy(self, depth, old_order=False, amount=False):
        info = self.get_trade_info(depth, 'buy', amount)
        if not info:
            return False
        api_resp = await self.trade('buy', info)
        if not api_resp:
            return False
        info['api'] = json.loads(utils.dumps(api_resp))
        order = await self.add_order(info)

        self.print_order(info, 'buy', old_order)
        info['id'] = order.id
        return info

    @classmethod
    def get_fee(cls, fee, delta):
        return 1 + (delta*(fee)/100)

    @classmethod
    def calc_money(cls, fee, amount, price, is_sell):
        if is_sell:
            sell_delta = -1
            buy_delta = 1
        else:
            sell_delta = 1
            buy_delta = -1
        return {
            'sell': sell_delta * amount,
            'buy': buy_delta * amount * price * cls.get_fee(fee, sell_delta)
        }

    def get_best_price(self, amount, price, is_sell, fee):
        money_change = self.calc_money(float(self.pair_info['fee']) + fee, amount, price, is_sell)
        return money_change['buy']

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

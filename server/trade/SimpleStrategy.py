import asyncio
import json, logging
import sqlalchemy as sa
from decimal import Decimal as D
from server import db
from server import utils 

class SimpleStrategy(object):

    OFFSET = 0
    LIMIT = 100000
    PAIR = 'btc_usd'
    FEE = D(0.2)
    logger = logging.getLogger(__name__)

    @classmethod
    def init_self(cls):
        return cls()

    @classmethod
    async def create(
            cls,
            engine,
            tradeApi,
            pubApi,
            is_demo=False,
            log=False,
            pair_list=False,
            fee = False
        ):
        self = cls.init_self()
        if fee:
            self.FEE = D(fee)
        if pair_list:
            self.PAIR = pair_list[0]
            self.PAIRS = self.PAIR,
        self.is_demo = is_demo
        self.log = log
        self.api = tradeApi
        self.pubApi = pubApi
        self.engine = engine;
        self.connection = await engine.acquire()
        self.prec = D(10) ** -6
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

    def print(self, *args):
        message = ' '.join(args)
        self.logger.info(message)
        if self.log:
            asyncio.ensure_future(self.log.broadcast({
                'message': message
            }))

    def get_order_table(self):
        return getattr(db, self.order_table)

    async def get_pair_info(self):
         resp = await self.pubApi.call('info')
         self.pair_info = resp['pairs'][self.PAIR]
         self.prec = D(10) ** -self.pair_info['decimal_places']
         return self.pair_info

    async def add_order(self, info, depth=False):
        if not info['api']:
            raise Exception('WTF dude?!?!')

        if self.is_demo:
            info['pub_date'] = depth['pub_date']

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

    async def get_balance(self):
        if self.is_demo:
            return False
        balnce_info = await self.api.call('getInfo')
        self.balance = balnce_info['funds']

    def get_new_amount(self, volume, directions, price, old_order):
        return self.pair_info['min_amount']

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
            is_sell = direction == 'sell'
            aposite_direction = 'buy' if is_sell else 'sell'
            change_info = self.calc_money(
                D(self.pair_info['fee']),
                D(info['amount']),
                D(info['price']),
                is_sell
            )
            self.balance[self.currency[direction]] += change_info[direction]
            self.balance[self.currency[aposite_direction]] += change_info[aposite_direction]
            return {
                "demo_order": "1",
                "funds": self.balance
            }
        api_resp = await self.api.call(
            'Trade',
            pair=info['pair'],
            type=direction,
            rate=info['price'],
            amount = D(info['amount']).quantize(self.prec)
        )
        if D(api_resp['received']) < info['amount']:
            self.print('CancelOrder {}'.format(
                api_resp['order_id']
            ))
            try:
                result = await self.api.call(
                    'CancelOrder',
                    order_id = api_resp['order_id']
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
            self.print('{} before {} now {} {}'.format(
                direction,
                old_order.price,
                info['price'],
                self.PAIR
                )
            )
        else:
            self.print('{} before init now {} {}'.format(
                direction,
                info['price'],
                self.PAIR
                )
            )

    def get_trade_info(self, depth, direction, amount=False, old_order=False):
        is_sell = direction == 'sell'
        currency = self.currency[direction]
        price, volume = depth['bids' if is_sell else 'asks'][0]
        info_amount = amount if amount else self.get_new_amount(D(volume), direction, price, old_order)
        money = info_amount if is_sell else D(price) * info_amount
        if self.balance[currency] < money:
            self.print('{} Low balance {} need more {} {}'.format(
                self.PAIR,
                self.balance[currency],
                (money - D(self.balance[currency])),
                currency,
                )
            )
            return 
        info = self.get_order_info(price, info_amount, is_sell)
        return info
        
    async def sell(self, depth, old_order=False, amount=False, print_info=1):
        info = self.get_trade_info(depth, 'sell', amount, old_order)
        if not info:
            return False
        api_resp = await self.trade('sell', info)
        if not api_resp:
            return False
        info['api'] = json.loads(utils.dumps(api_resp))
        order = await self.add_order(info, depth)
        info['id'] = order.id

        if print_info:
            self.print_order(info, 'sell', old_order)
        return info


    async def buy(self, depth, old_order=False, amount=False, print_info=1):
        info = self.get_trade_info(depth, 'buy', amount, old_order)
        if not info:
            return False
        api_resp = await self.trade('buy', info)
        if not api_resp:
            return False
        info['api'] = json.loads(utils.dumps(api_resp))
        order = await self.add_order(info, depth)
        info['id'] = order.id

        if print_info:
            self.print_order(info, 'buy', old_order)
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

    def get_best_price(self, amount, price, is_sell, fee=0):
        money_change = self.calc_money(D(self.pair_info['fee']) + fee, amount, price, is_sell)
        return money_change['buy']

    async def tick(self, resp, pair, balance=False, connection=False):
        if not pair == self.PAIR:
            return
        if connection:
            self.connection = connection
        self.depth = resp
        if not balance:
            await self.get_balance()
        else:
            self.balance = balance['funds']
        order = await self.get_order()
        if not order:
            self.print('init order is {}'.format(order))
            for currency, amount in self.balance.items():
                if amount > 0:
                    await self.sell(resp)
                    return
        else:
            old_money = self.get_best_price(
                D(self.order.amount),
                D(self.order.price),
                True
            )
            if order.is_sell:
                best_price = self.get_best_price(
                    D(self.order.amount),
                    D(resp['asks'][0][0]),
                    False,
                    self.FEE
                )
                if not self.is_demo:
                    self.print('buy', old_money, resp['asks'][0][0], best_price) 
                if old_money > best_price:
                    await self.buy(resp, self.order)
            else:
                best_price = self.get_best_price(
                    D(self.order.amount),
                    D(resp['bids'][0][0]),
                    True,
                    self.FEE
                )
                if not self.is_demo:
                    self.print('sell', old_money, resp['bids'][0][0], best_price) 
                if old_money < best_price:
                    await self.sell(resp, self.order)

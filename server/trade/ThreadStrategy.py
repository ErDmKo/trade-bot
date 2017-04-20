from server import db
import sqlalchemy as sa
from decimal import Decimal as D
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .SimpleStrategy import SimpleStrategy

class OrderThread(object):

    FLAG_NAME = 'is_finished'

    def __init__(self, order, conn, table):
        self.order = order
        self.table = table
        self.connection = conn

    def get(self, attr):
        return getattr(self.order, attr)

    def set(self, attr, value):
        setattr(self.order, attr, value)
        return self.get(attr)

    def get_order(self):
        return self.order

    async def update_by_id(self, id, **kw):
        return await self.connection.execute(
                self.table
                    .update()
                    .where(self.table.c.id == id)
                    .values(**kw)
        )

    async def merge(self, order):
        return await self.update_by_id(self.order.id,
            extra = sa.cast(
                sa.cast(func.coalesce(self.table.c.extra, '{}'), JSONB)
                .concat(func.jsonb_build_object(
                    self.FLAG_NAME, '1',
                    'merged', order.get('id')
                )), JSONB
            )
        )

    async def nextStep(self, nextOrder=False):
        if not nextOrder:
            raise Exception('WTF dude?!?!')

        return await self.update_by_id(self.order.id,
            extra = sa.cast(
                sa.cast(func.coalesce(self.table.c.extra, '{}'), JSONB)
                .concat(func.jsonb_build_object(
                    self.FLAG_NAME, '1',
                    'next', nextOrder['id'] if nextOrder else 'null'
                )), JSONB
            )
        )

class TrashHolder(object):

    THRESHOLD = 0.01

    def __init__(self, market):
        self.market = market
        self.sell_info = []
        self.buy_info = []

    def get_market_threshhold(self):
        return 1 - (float(self.market['bids'][0][0]) / float(self.market.depth['asks'][0][0]))

    def add_order(self, order_info):
        if order_info['order'].get('is_sell'):
            self.sell_info.append(order_info)
        else:
            self.buy_info.append(order_info)

    def get_min(self, direction):
        if not len(self.sell_info) and direction == 'sell' \
            or not len(self.buy_info) and direction == 'buy':
            return {
                'margin': 0
            }
        return min(
            getattr(self, 'sell_info' if direction == 'sell' else 'buy_info'),
            key=lambda i: i['margin']
        )

    def need_to_sell(self):
        order_info = self.get_min('sell')
        return order_info['margin'] > self.THRESHOLD

    def need_to_buy(self):
        order_info = self.get_min('buy')
        return order_info['margin'] > self.THRESHOLD

class ThreadStrategy(SimpleStrategy):

    LIMIT = 10000
    PAIR = 'btc_usd'
    ORDER_CLASS = OrderThread

    def get_threshhold(self, depth):
        return TrashHolder(depth)    

    async def get_order(self):
        self.order = None
        self.orders = []
        order_table = self.get_order_table()
        cursor = await self.connection.execute(
            order_table.select()
                .where(
                    (order_table.c.pair == self.PAIR) & 
                    (order_table.c.api != 'false') & 
                    (order_table.c.extra[self.ORDER_CLASS.FLAG_NAME].astext == '0')
                )
        )
        async for order in cursor:
            order_obj = self.ORDER_CLASS(order, self.connection, order_table)
            self.orders.append(order_obj)

        return self.orders

    def get_order_info(self, price, amount, is_sell):
        return dict(
            pair = self.PAIR,
            price = price,
            amount = amount,
            is_sell = is_sell,
            extra = {
                self.ORDER_CLASS.FLAG_NAME: "0"
            }
        )


    async def buy(self, depth, old_order=False, amount=False):
        new_order = await super().buy(depth, old_order, amount)
        if old_order and new_order:
            result = await old_order.nextStep(new_order)
        return new_order

    async def sell(self, depth, old_order=False, amount=False):
        new_order = await super().sell(depth, old_order)
        if old_order and new_order:
            result = await old_order.nextStep(new_order)
        return new_order

    def print_order(self, info, direction, old_order):
        if old_order:
            old_order = old_order.get_order()
        super().print_order(info, direction, old_order)

    async def start_new_thread(self, resp, direction=False):
        order = False
        for currency, amount in self.balance.items():
            if amount > 0 and currency in self.directions:
                if not direction:
                    direction = self.directions[currency]
                    self.print('Try to start new thread {}'.format(direction))
                    order = await getattr(self, direction)(resp)
                elif self.currency[direction] == currency:
                    self.print('Try to start new thread {}'.format(direction))
                    order = await getattr(self, direction)(resp)

                if order:
                    self.print('New thread currency {} price {} amount {} direction {}'.format(
                        currency,
                        order['price'],
                        order['amount'],
                        direction
                    ))
                    return

    async def tick(self, resp, balance=False, connection=False):
        thresh_hold = self.get_threshhold(resp)
        self.depth = resp
        await self.get_order()
        if not balance:
            await self.get_balance()
        else:
            self.balance = balance['funds']

        if not len(self.orders):
            self.print('init')
            return await self.start_new_thread(resp, 'sell')
        else:
            old_order = False
            for order in self.orders:

                if old_order and old_order.get('price') == order.get('price'):
                    await old_order.merge(order)

                old_money = self.get_best_price(
                    order.get('amount'),
                    order.get('price'),
                    order.get('is_sell'),
                    0
                )
                buy_money = self.get_best_price(
                    order.get('amount'),
                    float(resp['asks'][0][0]),
                    False,
                    self.FEE
                )
                sell_money = self.get_best_price(
                    order.get('amount'),
                    float(resp['bids'][0][0]),
                    True,
                    self.FEE
                )
                #print ('o {} b {} s {}'.format(old_money, buy_money, sell_money))
                if order.get('is_sell'):
                    # check previous sell and current market sell
                    margin = D(1 - (old_money / sell_money)).quantize(self.prec)
                    if not self.is_demo and abs(margin) < thresh_hold.THRESHOLD:
                        self.print(
                            'Try to buy - previous {} sell {} now {} with fee {} marign {}'.format(
                                order.get('id'),
                                old_money,
                                resp['asks'][0][0],
                                buy_money,
                                margin
                            )
                        )
                    thresh_hold.add_order({
                        'margin': margin,
                        'order': order
                    })

                    if old_money > -buy_money:
                        await self.buy(resp, order)
                else:
                    #previous buy and current market buy
                    margin = D((old_money / buy_money) - 1).quantize(self.prec)
                    if not self.is_demo and abs(margin) < thresh_hold.THRESHOLD:
                        self.print(
                            'Try to sell - previous {} buy {} now {} with fee {} marign {}'.format(
                                order.get('id'),
                                old_money,
                                resp['bids'][0][0],
                                sell_money,
                                margin
                            )
                        )
                    thresh_hold.add_order({
                        'margin': margin,
                        'order': order
                    })
                    if -old_money < sell_money:
                        await self.sell(resp, order)
                old_order = order

            if not self.is_demo:
                self.print('Threshhold margins Sell {} Buy {}'.format(
                    thresh_hold.get_min('sell')['margin'],
                    thresh_hold.get_min('buy')['margin']
                ))

            if  thresh_hold.need_to_sell():
                order_info = thresh_hold.get_min('sell')
                self.print('Sell last order price {} margin {} biger then {}'.format(
                    order_info['order'].get('price'),
                    order_info['margin'],
                    thresh_hold.THRESHOLD
                ))
                await self.start_new_thread(resp, 'sell')
            if thresh_hold.need_to_buy():
                order_info =thresh_hold.get_min('buy')
                self.print('Buy price {} margin {} biger then {}'.format(
                    order_info['order'].get('price'),
                    thresh_hold.get_min('buy')['margin'],
                    thresh_hold.THRESHOLD
                ))
                await self.start_new_thread(resp, 'buy')

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

    async def merge(self, order):
        order_table = self.table
        return await self.connection.execute(
                order_table
                    .update()
                    .where(order_table.c.id == self.order.id)
                    .values(
                        extra = sa.cast(
                            sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                            .concat(func.jsonb_build_object(
                                self.FLAG_NAME, '1',
                                'merged', order.get('id')
                            )), JSONB
                        )
                    ) 
        )

    async def nextStep(self, nextOrder=False):
        if not nextOrder:
            raise Exception('WTF dude?!?!')

        order_table = self.table
        return await self.connection.execute(
                order_table
                    .update()
                    .where(order_table.c.id == self.order.id)
                    .values(
                        extra = sa.cast(
                            sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                            .concat(func.jsonb_build_object(
                                self.FLAG_NAME, '1',
                                'next', nextOrder.id if nextOrder else 'null'
                            )), JSONB
                        )
                    )
        )

class ThreadStrategy(SimpleStrategy):

    LIMIT = 10000
    PAIR = 'btc_usd'
    FEE = 0.1

    THRESHOLD = 0.01

    FLAG_NAME = 'is_finished'

    @classmethod
    def init_self(cls):
        return ThreadStrategy()

    def get_market_threshhold(self, depth):
        return 1 - (depth['bids'][0][0] / depth['asks'][0][0])

    def get_threshhold(self, depth):
        return max(
            self.THRESHOLD,
            self.get_market_threshhold(depth) 
        )

    async def get_order(self):
        self.order = None
        self.orders = []
        order_table = self.get_order_table()
        cursor = await self.connection.execute(
            order_table.select()
                .where(
                    (order_table.c.pair == self.PAIR) & 
                    (order_table.c.extra[self.FLAG_NAME].astext == '0')
                )
        )
        async for order in cursor:
            order_obj = OrderThread(order, self.connection, order_table)
            self.orders.append(order_obj)

        return self.orders

    def get_order_info(self, price, amount, is_sell):
        return dict(
            pair = self.PAIR,
            price = price,
            amount = amount,
            is_sell = is_sell,
            extra = {
                self.FLAG_NAME: "0"
            }
        )


    async def buy(self, depth, old_order=False):
        new_order = await super().buy(depth, old_order)
        if old_order and new_order:
            result = await old_order.nextStep(new_order)
        return new_order

    async def sell(self, depth, old_order=False):
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
                    self.print('New thread was started currency {} amount {} direction {}'.format(
                        currency,
                        amount,
                        direction
                    ))
                    return

    async def tick(self, resp):
        self.depth = resp
        await self.get_order()
        await self.get_balance()
        sell_margins = []
        buy_margins = []

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
                    True
                )
                if order.get('is_sell'):
                    best_price = self.get_best_price(
                        order.get('amount'),
                        resp['asks'][0][0],
                        False
                    )
                    margin = D(1 - (old_money / best_price)).quantize(self.prec)
                    if not self.is_demo and abs(margin) < self.get_threshhold(resp):
                        self.print(
                            'Try to buy - previous sell {} now {} with fee {} marign {}'.format(
                                old_money,
                                resp['asks'][0][0],
                                best_price,
                                margin
                            )
                        )
                    sell_margins.append(margin)

                    if old_money > best_price:
                        await self.buy(resp, order)
                else:
                    best_price = self.get_best_price(
                        order.get('amount'),
                        resp['bids'][0][0],
                        True
                    )
                    margin = D((old_money / best_price) - 1).quantize(self.prec)
                    if not self.is_demo and abs(margin) < self.get_threshhold(resp):
                        self.print(
                            'Try to sell - previous buy {} now {} need {} marign {}'.format(
                                old_money,
                                resp['bids'][0][0],
                                best_price,
                                margin
                            )
                        )
                    buy_margins.append(margin)
                    if old_money < best_price:
                        await self.sell(resp, order)
                old_order = order

            thresh_hold = self.get_threshhold(resp)
            self.print('Threshhold {} market {} {} / {}'.format(
                thresh_hold,
                self.get_market_threshhold(resp),
                resp['bids'][0][0], 
                resp['asks'][0][0]
            ))
            if len(sell_margins) and min(sell_margins) > thresh_hold:
                self.print('Sell margin {} biger then {}'.format(
                    min(sell_margins),
                    thresh_hold
                ))
                await self.start_new_thread(resp, 'sell')
            if len(buy_margins) and min(buy_margins) > thresh_hold:
                self.print('Buy margin {} biger then {}'.format(
                    min(buy_margins),
                    thresh_hold
                ))
                await self.start_new_thread(resp, 'buy')

            sell_margins = []
            buy_margins = []


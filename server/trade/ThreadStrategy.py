from server import db
import sqlalchemy as sa
import logging
from decimal import Decimal as D
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .SimpleStrategy import SimpleStrategy

class OrderThread(object):

    FLAG_NAME = 'is_finished'
    logger = logging.getLogger(__name__)

    def __init__(self, order, conn, table, prec):
        self.order = order
        self.table = table
        self.connection = conn
        self.prec = prec

    def get(self, attr):
        return getattr(self.order, attr)

    def set(self, attr, value):
        setattr(self.order, attr, value)
        return self.get(attr)

    def get_order(self):
        return self.order

    async def read(self):
        update_order = await self.get_by_id(self.order.id)
        async for order in update_order:
            self.order = order

    async def get_by_id(self, id):
        return await self.connection.execute(
            self.table.select().where(self.table.c.id == id)
        )

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

    '''
    We start new thread
    if market prices is go away
    form cerrent threads
    0.01 - 1%
    '''
    THRESHOLD = 0.015

    def __init__(self, market):
        self.market = market
        self.sell_info = []
        self.buy_info = []

    def get_market_threshhold(self):
        return 1 - (D(self.market['bids'][0][0]) / D(self.market.depth['asks'][0][0]))

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
    logger = logging.getLogger(__name__)

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
            order_obj = self.ORDER_CLASS(
                order,
                self.connection,
                order_table,
                self.prec
            )
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
        new_order = await super().buy(depth, old_order, amount, 0)
        if old_order and new_order:
            result = await old_order.nextStep(new_order)
            self.print_order(new_order, 'buy', old_order)
        return new_order

    async def sell(self, depth, old_order=False, amount=False):
        new_order = await super().sell(depth, old_order, amount, 0)
        if old_order and new_order:
            result = await old_order.nextStep(new_order)
            self.print_order(new_order, 'sell', old_order)
        return new_order

    def print_order(self, info, direction, old_order):
        if old_order:
            old_order = old_order.get_order()
        super().print_order(info, direction, old_order)

    async def start_new_thread(self, resp, direction=False):
        order = False
        self.print('init {}'.format(self.PAIR))
        for currency, amount in self.balance.items():
            if not direction:
                direction = self.directions.get(currency)
            if currency in self.directions and amount > 0:
                if self.currency[direction] == currency:
                    self.print('Try to start new thread {}'.format(direction))
                    order = await getattr(self, direction)(
                        resp, 
                        amount=D(self.pair_info['min_amount'])
                    )

                if order:
                    self.print('New thread currency {} price {} amount {} direction {}'.format(
                        currency,
                        order['price'],
                        order['amount'],
                        direction
                    ))
                    return

    async def tick(self, resp, pair, balance=False, connection=False):
        if not pair == self.PAIR:
            return
        await self.connection.close()
        self.connection = await self.engine.acquire()
        thresh_hold = self.get_threshhold(resp)
        self.depth = resp
        await self.get_order()
        if not balance:
            await self.get_balance()
        else:
            self.balance = balance['funds']

        if not len(self.orders):
            return await self.start_new_thread(resp)
        else:
            old_order = False
            for order in self.orders:

                if old_order \
                    and old_order.get('price') == order.get('price')  \
                    and old_order.get('is_sell')  == order.get('is_sell'):
                    await old_order.merge(order)
                    break

                # spended money
                old_money = self.get_best_price(
                    D(order.get('amount')),
                    D(order.get('price')),
                    order.get('is_sell'),
                    0
                )
                # if we buy now
                buy_money = self.get_best_price(
                    D(order.get('amount')),
                    D(resp['asks'][0][0]),
                    False,
                    self.FEE
                )
                # if we sell now
                sell_money = self.get_best_price(
                    D(order.get('amount')),
                    D(resp['bids'][0][0]),
                    True,
                    self.FEE
                )
                #print ('o {} b {} s {}'.format(old_money, buy_money, sell_money))
                if order.get('is_sell'):
                    # check previous sell and current market sell
                    margin = D(1 - (old_money / sell_money)).quantize(self.prec)
                    if not self.is_demo and abs(margin) < thresh_hold.THRESHOLD:
                        self.print(
                            'Try to buy - previous {} sell {} now {} with fee {} marign {} {}'.format(
                                order.get('id'),
                                old_money.quantize(self.prec),
                                resp['asks'][0][0],
                                buy_money.quantize(self.prec),
                                margin,
                                self.PAIR
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
                            'Try to sell - previous {} buy {} now {} with fee {} marign {} {}'.format(
                                order.get('id'),
                                old_money.quantize(self.prec),
                                resp['bids'][0][0],
                                sell_money.quantize(self.prec),
                                margin,
                                self.PAIR
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

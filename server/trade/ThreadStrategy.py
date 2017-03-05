from server import db
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .SimpleStrategy import SimpleStrategy

class ThreadStrategy(SimpleStrategy):

    LIMIT = 10000
    PAIR = 'btc_usd'
    FEE = 0.1

    FLAG_NAME = 'is_finished'

    @classmethod
    def init_self(cls):
        return ThreadStrategy()

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
            self.orders.append(order)

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

    async def finish_order(self, order):
        order_table = self.get_order_table()
        return await self.connection.execute(
                order_table
                    .update()
                    .where(order_table.c.id == order.id)
                    .values(
                        extra = sa.cast(
                            sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                            .concat(func.jsonb_build_object(self.FLAG_NAME, '1')), JSONB
                        )
                    ) 
        )

    async def buy(self, depth, old_order=False):
        new_order = await super().buy(depth, old_order)
        if old_order:
            result = await self.finish_order(old_order)
        return new_order

    async def sell(self, depth, old_order=False):
        new_order = await super().sell(depth, old_order)
        if old_order:
            result = await self.finish_order(old_order)
        return new_order

    async def tick(self, resp):
        self.depth = resp
        await self.get_order()

        if not len(self.orders):
            print('init')
            for currency, amount in self.balance.items():
                if amount > 0:
                    await self.sell(resp)
                    return
        else:
            for order in self.orders:
                old_money = self.get_best_price(order.amount, order.price, True)
                if order.is_sell:
                    best_price = self.get_best_price(order.amount, resp['asks'][0][0], False)
                    if not self.is_demo:
                        print('buy', old_money, resp['asks'][0][0], best_price) 
                    if old_money > best_price:
                        await self.buy(resp, order)
                else:
                    best_price = self.get_best_price(order.amount, resp['bids'][0][0], False)
                    if not self.is_demo:
                        print('sell', old_money, resp['bids'][0][0], best_price) 
                    if old_money < best_price:
                        await self.sell(resp, order)

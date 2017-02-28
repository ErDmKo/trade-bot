from .SimpleStrategy import SimpleStrategy

class ThreadStrategy(SimpleStrategy):

    LIMIT = 10000
    PAIR = 'btc_usd'
    FEE = 0.1

    async def get_order(self):
        self.orders = []
        cursor = await self.connection.execute(
            db.order.select()
                .where(
                    (db.order.c.pair == self.PAIR) & 
                    (db.order.c.extra['is_finish'].astext == '0')
                )
        )
        async for order in cursor:
            self.orders.append(order)

        return self.orders

    async def tick(self, resp):
        self.depth = resp
        await self.get_order()

        if self.orders:
            for order in self.orders:
                old_money = self.get_best_price(order.amount, order.price, True)
                if order.is_sell:
                    best_price = self.get_best_price(order.amount, resp['asks'][0][0], False)
                    print('buy', old_money, resp['asks'][0][0], best_price) 
                    if old_money > best_price:
                        await self.buy(resp, order)
                else:
                    best_price = self.get_best_price(order.amount, resp['bids'][0][0], False)
                    print('sell', old_money, resp['asks'][0][0], best_price) 
                    if old_money < best_price:
                        await self.sell(resp, order)

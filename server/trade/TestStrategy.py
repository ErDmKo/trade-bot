from .ThreadStrategy import ThreadStrategy


class TestStrategy(ThreadStrategy):
    async def order_cancel(self):
        await self.sell({
            'bids': [
                [9999]
            ]
        })

    async def tick(self, resp, balance):
        result = await self.api.call(
            'CancelOrder',
            order_id=1679745692
        )
        print (result)

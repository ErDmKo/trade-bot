import logging
from .VolumeStrategy import VolumeStrategy


class MultiplePairs(object):

    STRATEGY = VolumeStrategy
    STORE = {}
    OFFSET = 0
    LIMIT = 100000
    PAIRS = 'eth_usd', 'eth_btc', 'btc_usd',
    logger = logging.getLogger(__name__)

    @classmethod
    async def create(cls,
                     engine,
                     tradeApi,
                     pubApi,
                     strategy=False,
                     is_demo=False,
                     log=False,
                     fee=False,
                     pair_list=[]):

        self = cls()

        if strategy:
            self.strategy = strategy

        self.is_demo = is_demo
        for pair in pair_list:
            self.STORE[pair] = await self.STRATEGY.create(
                engine,
                tradeApi,
                pubApi,
                is_demo=is_demo,
                log=log,
                fee=fee,
                pair_list=(pair,)
            )
        return self

    async def tick(self, resp, pair, balance=False):
        if self.STORE.get(pair):
            # self.logger.info(pair)
            await self.STORE[pair].tick(resp, pair, balance)
            if self.is_demo:
                self.balance = self.STORE[pair].balance

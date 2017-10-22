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
    def init_self(cls):
        return cls()

    @classmethod
    async def create(cls,
        connection,
        tradeApi,
        pubApi,
        strategy=False,
        is_demo=False,
        log=False,
        pair_list=[]):

        self = cls.init_self()

        if strategy:
            self.strategy = strategy

        self.is_demo = is_demo
        for pair in pair_list:
            self.STORE[pair] = await self.STRATEGY.create(
                connection,
                tradeApi,
                pubApi,
                is_demo = is_demo,
                log = log,
                pair_list = (pair,)
            )
        return self

    async def tick(self, resp, pair, balance=False):
        if self.STORE.get(pair):
            self.logger.info(pair)
            await self.STORE[pair].tick(resp, pair, balance)
            if self.is_demo:
                self.balance = self.STORE[pair].balance

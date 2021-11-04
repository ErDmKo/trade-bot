import asyncio
import logging
import pathlib
import tinvest as ti
from tinvest.schemas import BrokerAccountType
from random import randrange

from server.utils import load_config

logger = logging.getLogger(__name__)

class TinkoffClient(object):

    def __init__(self, asyncClient):
        logger.info('create broker client')
        self.asyncClient = asyncClient
        self.accounts = []

    async def initAsync(self):
        response = await self.asyncClient.get_accounts()
        for account in response.payload.accounts:
            accType = account.broker_account_type
            if BrokerAccountType.tinkoff == accType:
                self.accounts.append({
                    'type': accType,
                    'id': account.broker_account_id
                })

        if not len(self.accounts):
            raise Exception('No accounts for trade')

        self.currentAccount = self.accounts[0]['id']

    def call(self, method, *args, **kwargs):
        instanceMethod = getattr(self, method, None)
        if not instanceMethod:
            raise Exception(f'method "{method}" does\'t exist')
        return instanceMethod(*args, **kwargs)

    async def depth(self):
        return {
            'pairName': {
                'sale': [1,2,3,4]
            }
        }

    async def log(self):
        return {
            'message': 'Log started'
        }

    async def getInfo(self):
        response = await self.asyncClient.get_portfolio(self.currentAccount)
        dictResp = {}
        for position in response.payload.positions:
            dictResp[position.ticker] = {
                'amount': position.balance,
                'title': position.name,
                'currency': position.average_position_price.currency.name
            }
        return {
            'funds': dictResp
            }

async def getAsyncClient(token):
    asyncClient = ti.AsyncClient(token)
    appClient = TinkoffClient(asyncClient)
    await appClient.initAsync()
    return appClient


async def checkAsyncClient(token):
    async with ti.AsyncClient(token) as client:
        response = await client.get_portfolio()
        print(response.payload)


async def stream(token):
    async with ti.Streaming(token) as streaming:
        await streaming.candle.subscribe('BBG0013HGFT4', ti.CandleResolution.min1)
        await streaming.orderbook.subscribe('BBG0013HGFT4', 5)
        await streaming.instrument_info.subscribe('BBG0013HGFT4')
        async for event in streaming:
            print(event)


def main():
    conf = load_config(str(pathlib.Path('.') / 'config' / 'base.yaml'))
    token = conf.get('api', {}).get('pubtoken')
    asyncio.run(checkAsyncClient(token))

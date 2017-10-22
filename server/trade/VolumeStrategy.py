from decimal import Decimal as D
import sqlalchemy as sa
import logging
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from .ThreadStrategy import ThreadStrategy, OrderThread

class VolumeThread(OrderThread):

    FLAG_NAME = 'is_exceed'
    logger = logging.getLogger(__name__)

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
        order_table = self.table
        await self.read()
        new_amount = (D(self.order.extra['amount']) - nextOrder['amount']).quantize(self.prec)
        if new_amount <= 0:
            await self.update_by_id(self.order.id,
                extra = sa.cast(
                    sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                    .concat(func.jsonb_build_object(
                        self.FLAG_NAME, '1',
                        'amount', str(new_amount)
                    )), JSONB
                )
            )
        else:
            await self.update_by_id(self.order.id, 
                extra = sa.cast(
                    sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                    .concat(func.jsonb_build_object(
                        'amount', str(new_amount)
                    )), JSONB
                )
            )
        await self.read()
        return await self.update_by_id(nextOrder['id'],
            extra = sa.cast(
                sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                .concat(func.jsonb_build_object(
                    'parent', self.order.id,
                )), JSONB
            )
        )

class VolumeStrategy(ThreadStrategy):

    LIMIT = 20000
    ORDER_CLASS = VolumeThread
    MAX_VOLUME = D(5) # % form balance less precent is hight accuracy and low speed

    async def add_order(self, info, depth):
        if not info['api']:
            raise Exception('WTF dude?!?!')

        if self.is_demo:
            info['pub_date'] = depth['pub_date']

        info['extra'] = {
            self.ORDER_CLASS.FLAG_NAME: '0',
            'amount': str(info['amount'])
        }

        result = await self.connection.execute(
            self.get_order_table().insert().values(**info)
        )
        result_info = await result.first()
        return result_info

    def print_order(self, info, direction, old_order):
        if old_order:
            self.print('{} before id {} price {} amount left {} new child price {} amount {} {}'.format(
                direction,
                old_order.get('id'),
                old_order.get('price'),
                old_order.get('extra').get('amount'),
                info['price'],
                info['amount'],
                self.PAIR
                )
            )
        else:
            self.print('{} before init now price {} amount {} {}'.format(
                direction,
                info['price'],
                info['amount'],
                self.PAIR
                )
            )

    def get_new_amount(self, volume, direction, price, old_order):
        '''
        direction - sell buy
        volume - market volume
        price - market price
        old_order - VolumeThread instanse
        '''
        balance = {
            'sell': D(self.balance[self.currency['sell']]),
            'buy': D(self.balance[self.currency['buy']]) / D(price)
        }
        '''
        print('sell - {sell} buy - {buy}'.format(**amounts))
        print('selected - {}'.format(amounts[direction]))
        '''
        new_volume = min([
            D(D(old_order.get('amount')) * (D(1) + self.MAX_VOLUME)).quantize(self.prec),
            volume,
            (balance[direction] * (self.MAX_VOLUME/100)).quantize(self.prec)
        ])
        return max([
            D(self.pair_info['min_amount']),
            new_volume
        ])


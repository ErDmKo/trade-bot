from decimal import Decimal as D
import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from .ThreadStrategy import ThreadStrategy, OrderThread

class VolumeThread(OrderThread):
    FLAG_NAME = 'is_exceed'

    async def nextStep(self, nextOrder=False):
        if not nextOrder:
            raise Exception('WTF dude?!?!')

        order_table = self.table
        new_amount = D(self.order.amount) - nextOrder['amount']
        if new_amount.quantize(self.prec) <= 0:
            await self.update_by_id(self.order.id,
                extra = sa.cast(
                    sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                    .concat(func.jsonb_build_object(
                        self.FLAG_NAME, '1',
                        'amount', 0
                    )), JSONB
                )
            )
        else:
            await self.update_by_id(self.order.id, 
                extra = sa.cast(
                    sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                    .concat(func.jsonb_build_object(
                        'amount', new_amount
                    )), JSONB
                )
            )
        update_order = await self.get_by_id(self.order.id)
        async for order in update_order:
            self.order = order
        return await self.update_by_id(nextOrder['id'],
            extra = sa.cast(
                sa.cast(func.coalesce(order_table.c.extra, '{}'), JSONB)
                .concat(func.jsonb_build_object(
                    'parent', self.order.id
                )), JSONB
            )
        )

class VolumeStrategy(ThreadStrategy):

    LIMIT = 100000
    ORDER_CLASS = VolumeThread
    MAX_VOLUME = D(0.5) # % form balance

    def print_order(self, info, direction, old_order):
        if old_order:
            self.print('{} before {} amount left {} new child price {} amount {}'.format(
                direction,
                old_order.get('price'),
                old_order.get('extra').get('amount'),
                info['price'],
                info['amount']
                )
            )
        else:
            self.print('{} before init now price {} amount {}'.format(
                direction,
                info['price'],
                info['amount']
                )
            )
    
    def get_new_amount(self, currency, amount, volume):
        '''
            amount is from new thread
            volume is from market best offer
        '''
        if amount:
            return amount
        max_volume = D(self.balance[self.currency['sell']] * (self.MAX_VOLUME/100)).quantize(self.prec)
        new_volume = min([
            volume,
            max_volume
        ])
        return max([
            D(self.pair_info['min_amount']),
            new_volume
        ])


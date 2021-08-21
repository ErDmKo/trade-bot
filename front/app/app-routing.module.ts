import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { IndexComponent } from './index.component'
import { OrderComponent } from './order.component'
import { TradeLogComponent } from './trade-log.component'
import { OrderBookComponent } from './order-book.component'
import { OrderDetailComponent } from './order-detail.component'

const routes: Routes = [{ 
        path: '', 
        redirectTo: '/order',
        pathMatch: 'full' 
    }, { 
        path: 'order', 
        component: OrderComponent,
        data: {
            title: 'Orders'
        }
    }, {
        path: 'order/:id',
        component: OrderDetailComponent,
        data: {
            title: 'Order details'
        }
    }, { 
        path: 'log',
        component: TradeLogComponent,
        data: {
            title: 'Trade log'
        }
    }, { 
        path: 'stat',
        component: OrderBookComponent,
        data: {
            title: 'Stats from history'
        },
    },
]

@NgModule({
    imports: [ RouterModule.forRoot(routes, { relativeLinkResolution: 'legacy' }) ],
    exports: [ RouterModule ]
})
export class AppRoutingModule {}

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { IndexComponent } from './index.component'
import { OrderComponent } from './order.component'
import { TradeLogComponent } from './trade-log.component'
import { OrderBookComponent } from './order-book.component'
import { OrderDetailComponent } from './order-detail.component'

const routes: Routes = [
    { path: '', redirectTo: '/order', pathMatch: 'full' },
    { path: 'order', component: OrderComponent },
    { path: 'order/:id', component: OrderDetailComponent },
    { path: 'log', component: TradeLogComponent },
    { path: 'stat', component: OrderBookComponent },
]

@NgModule({
    imports: [ RouterModule.forRoot(routes) ],
    exports: [ RouterModule ]
})
export class AppRoutingModule {}

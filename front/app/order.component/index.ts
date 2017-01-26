import { Component, ViewEncapsulation } from '@angular/core';
import { AppState } from '../app.service';
import { OrderService } from './order.service';

@Component({
    selector: 'order',
    styleUrls: [
        './style.css'
    ],
    templateUrl: './template.html',
    providers: [
        OrderService
    ]
})
export class OrderComponent {
    private orders: any[];
    errorMessage: string;

    constructor(
        public appState: AppState,
        private orderService: OrderService
    ) {
    }
    removeOrder(id) {
        this.orderService
            .removeOrder(id)
            .subscribe(
                info => this.orders = info.orders,
                error => this.errorMessage = <any>error
            )
    }
    ngOnInit () {
        this.orderService
            .getList()
            .subscribe(
                info => this.orders = info.orders,
                error => this.errorMessage = <any>error
            );
    }
    onOrder() {
        this.orderService
            .onOrder(10, 'btc_usd')
            .subscribe(info => {
                this.orders = info.orders;
            })
    }
}

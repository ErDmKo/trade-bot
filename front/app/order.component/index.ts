import { Component, ViewEncapsulation } from '@angular/core';
import { AppState } from '../app.service';
import { OrderService } from './order.service';

const ROWS: Array<{
    title: string,
    key: string
    func?: Function
}> = [{
    title: 'id',
    key: 'id'
}, {
    title: 'date',
    key: 'pub_date',
}, {
    title: 'direction',
    key: 'is_sell',
    func: (val) => val ? 'sell' : 'buy'
}, {
    title: 'price',
    key: 'price'
}, {
    title: 'pair',
    key: 'pair'
}].map((col) => Object.assign({
    func: (val) => val
}, col));

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
    rows = ROWS;

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

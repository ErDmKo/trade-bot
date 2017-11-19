import { Component } from '@angular/core';
import { AppState } from '../app.service';
import { OrderService } from './order.service';

interface Col {
    title: string,
    key: string
    func?: Function
}

const ROWS: Array<Col> = [{
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
}, {
    title: 'parent',
    key: 'extra',
    func: val => val.parent
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

    isLink(col: Col) {
        return ['id', 'extra'].includes(col.key);
    }

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

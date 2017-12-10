import { Component, Input } from '@angular/core';
import { AppState } from '../app.service';
import { OrderService } from './order.service';
import { ActivatedRoute, Params } from '@angular/router';

interface Col {
    title: string,
    key: string
    func?: Function
}
interface Pair {
    title: string,
    id: number
}
const PAIRS: Array<Pair> = [{
    id: null,
    title: 'All'
}, {
    id: 1,
    title: 'btc_usd'
}, {
    id: 2,
    title: 'eth_usd'
}, {
    id: 3,
    title: 'eth_btc'
}]

const ROWS: Array<Col> = [{
    title: 'id',
    key: 'id'
}, {
    title: 'date',
    key: 'pub_date',
}, {
    title: 'amount',
    key: 'amount',
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
    pairs = PAIRS;
    selectedPair: Pair = PAIRS[0];
    @Input() parent: number;


    isLink(col: Col) {
        return ['id', 'extra'].includes(col.key);
    }

    constructor(
        public appState: AppState,
        private orderService: OrderService,
        private route: ActivatedRoute
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
        this.route.params.forEach((params: Params) => {
            this.orderService
                .getList({
                    parent: params.id
                })
                .subscribe(
                    info => this.orders = info.orders,
                    error => this.errorMessage = <any>error
                );
        })
    }
    applyFilter(newVal) {
        this.selectedPair = newVal;
        this.orderService
            .getList(Object.assign({
                parent: this.parent
            }, newVal.id && {
                pair: newVal.title,
            }))
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

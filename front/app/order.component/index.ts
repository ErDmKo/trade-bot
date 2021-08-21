import { Component, Input } from '@angular/core';
import { AppState } from '../app.service';
import { OrderService } from './order.service';
import { ActivatedRoute, Params } from '@angular/router';
import * as moment from 'moment';

interface Col {
    title: string,
    key: string
    func?: Function
}
export interface Filtred {
    title: string
    value?: string
    id: number
}
export interface Pair extends Filtred {
}
interface Page {
    no: number,
    selected: boolean
}
interface ExceedState extends Filtred {
}
interface Filter {
    [key: string]: Filtred
}
const IS_SELL: Array<Filtred> = [{
    id: null,
    title: 'Buy and Sell'
}, {
    id: 1,
    value: '1',
    title: 'Sell'
}, {
    id: 2,
    value: '0',
    title: 'Buy'
}]
const EXCEED: Array<ExceedState> = [{
    id: null,
    title: 'Exceeded and Not'
}, {
    id: 1,
    value: '1',
    title: 'Exceeded'
}, {
    id: 2,
    value: '0',
    title: 'Not exceeded'
}]
export const PAIRS: Array<Pair> = [{
    id: null,
    title: 'All pairs'
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
    key: 'id',
}, {
    title: 'date',
    key: 'pub_date',
    func: (val) => moment(val).fromNow(true)
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
        './style.scss'
    ],
    templateUrl: './template.html',
    providers: [
        OrderService
    ]
})
export class OrderComponent {
    orders: any[];
    errorMessage: string;
    pages: Page[];
    rows = ROWS;
    pageSize = 30;
    page = 0;
    //shit code
    filter: Filter = {
        pair: PAIRS[0],
        is_exceed: EXCEED[0],
        is_sell: IS_SELL[0]
    };
    pairs = PAIRS;
    exceededList = EXCEED;
    sellList = IS_SELL;
    // ----
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
                (info: any) => this.orders = info.orders,
                error => this.errorMessage = <any>error
            )
    }
    ngOnInit () {
        this.route.params.forEach((params: Params) => {
            this.orderService
                .getList(this.getListParams({
                    parent: params.id,
                }))
                .subscribe(
                    info => {
                        this.page = 0;
                        this.setState(info);
                    },
                    error => this.errorMessage = <any>error
                );
        })
    }
    setState(info) {
        this.orders = info.orders;
        this.pages = Array.from(Array(Math.ceil(info.meta.total / this.pageSize)).keys())
            .map(i => ({
                no: i + 1,
                selected: i == this.page
            }));
    }
    getListParams(base?) {
        return {
            ...(base || {}),
            parent: this.parent,
            offset: this.pageSize * this.page,
            limit: this.pageSize
        }
    }
    applyFilter(filter = {}) {
        this.filter = Object.assign(this.filter, filter);
        if (Object.keys(filter).length) {
            this.page = 0;
        }
        this.orderService
            .getList(Object.assign(this.getListParams(), Object.keys(this.filter)
               .reduce((resultFilter, key) => {
                   const info = this.filter[key];
                   if (info.id !== null ) {
                       resultFilter[key] = info.value !== undefined ? info.value : info.title
                   }
                   return resultFilter
               }, {} as {[key: string]: string})
            ))
            .subscribe(
                info => this.setState(info),
                error => this.errorMessage = <any>error
            );
    }
    selectPage(page) {
        this.page = page.no - 1;
        this.applyFilter();
    }
}

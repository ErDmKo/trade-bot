import { Component } from '@angular/core';
import { OrderBookService } from './order-book.service'
import { HistoryService } from './history.service'
import { ActivatedRoute, Params } from '@angular/router';

import { AppState } from '../app.service';

@Component({
  selector: 'order-book',
  styleUrls: [
      './style.css'
  ],
  templateUrl: './template.html',
  providers: [
    OrderBookService,
    HistoryService
  ]
})
export class OrderBookComponent {
    private data: any[];
    errorMessage: string;
    private deph: any;

    constructor(
        public appState: AppState,
        private orderBookService: OrderBookService,
        private route: ActivatedRoute,
        private historyService: HistoryService
    ) {
    }
    ngOnInit () {
        this.orderBookService
            .getWsData()
            .subscribe(
                data => this.data = data,
                error => this.errorMessage = <any>error
            );
        this.route.params.forEach((params: Params) => {
            this.historyService
                .getList({
                    pair: 'eth_btc',
                    limit: 100,
                    group: 'minute',
                    from: '2018-05-12T00:00:00',
                    to: '2018-06-12T15:00:00'
                })
                .subscribe(
                    info => {
                        this.deph = info;
                    },
                    error => this.errorMessage = <any>error
                );
        })
    }
}

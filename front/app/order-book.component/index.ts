import { Component } from '@angular/core';
import { OrderBookService } from './order-book.service'

import { AppState } from '../app.service';

@Component({
  selector: 'order-book',
  styleUrls: [
      './style.css'
  ],
  templateUrl: './template.html',
  providers: [
    OrderBookService
  ]
})
export class OrderBookComponent {
    private data: any[];
    errorMessage: string;

    constructor(
        public appState: AppState,
        private orderBookService: OrderBookService
    ) {
    }
    ngOnInit () {
        this.orderBookService
            .getWsData()
            .subscribe(
                data => this.data = data,
                error => this.errorMessage = <any>error
            );
    }
}

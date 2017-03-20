import { Component } from '@angular/core';
import { TradeLogService } from './trade-log.service'

interface iLog {
    message: string
}


@Component({
  selector: 'trade-log',
  styleUrls: [
      './style.css'
  ],
  templateUrl: './template.html',
  providers: [
    TradeLogService
  ]
})
export class TradeLogComponent {
    private data: any[] = [];
    private errorMessage: string;

    constructor(
        private tradeLogService: TradeLogService
    ) {
    }

    public ngOnInit () {
        this.tradeLogService
            .getWsData()
            .subscribe(
                data => {
                    this.data.push(data);
                    this.data = this.data.slice(-30);
                },
                error => this.errorMessage = <any>error
            );
    }
}

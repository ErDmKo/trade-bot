import { Component, ViewEncapsulation } from '@angular/core';
import { BalanceService } from './balance.service'
import { AppState } from '../app.service';

@Component({
  selector: 'balance',
  providers: [],
  styleUrls: [
      './style.scss'
  ],
  templateUrl: './template.html'
})
export class BalanceComponent {
    data: Object;
    errorMessage: string;

    constructor(
        public appState: AppState,
        private balanceService: BalanceService
    ) {
    }
    ngOnInit () {
        this.balanceService
            .getWsData()
            .subscribe(
                data => this.data = data,
                error => this.errorMessage = <any>error
            );
    }
}

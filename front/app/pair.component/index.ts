import { Component, ViewEncapsulation } from '@angular/core';

import { AppState } from '../app.service';
import { PairService } from './pair.service';

@Component({
  selector: 'pair',
  providers: [
    PairService
  ],
  templateUrl: './template.html'
})
export class PairComponent {
    pairs: any[];
    errorMessage: string;

    constructor(
        public appState: AppState,
        private pairService: PairService
    ) {
    }
    ngOnInit () {
        this.pairService
            .getPairs()
            .subscribe(
                pairs => this.pairs = pairs,
                error => this.errorMessage = <any>error
            );
    }
}

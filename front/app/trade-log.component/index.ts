import { 
    Component,
    transition,
    state,
    style,
    trigger,
    animate
} from '@angular/core';
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
  ],
  animations: [
      trigger('flyInOut', [
          state('in', style({
              opacity: 1,
              transform: 'translateX(0)'
          })),
          transition('void => *', [
            style({
              opacity: 0,
              transform: 'translateX(-100%)'
            }),
            animate('0.2s ease-in')
          ]),
          transition('* => void', [
            animate('0.2s 10 ease-out', style({
              opacity: 0,
              transform: 'translateX(100%)'
            }))
          ])
      ])
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
                    this.data.splice(0, 0, data);
                    this.data = this.data.slice(0, 30);
                },
                error => this.errorMessage = <any>error
            );
    }
}

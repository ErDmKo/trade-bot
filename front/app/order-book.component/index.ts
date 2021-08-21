import { Component, ViewChild, ElementRef } from '@angular/core';
import { OrderBookService } from './order-book.service'
import { HistoryService } from './history.service'
import { ActivatedRoute, Params } from '@angular/router';
import { PAIRS, Filtred } from '../order.component'
import * as moment from 'moment';
// import * as Plotly from 'plotly.js/lib/core';
import { Moment, DurationInputArg1, DurationInputArg2 } from 'moment';

import { AppState } from '../app.service';
import { HttpParams } from '@angular/common/http';


interface Filter {
    pair: Filtred,
    group: Filtred,
    from?: Moment,
    to?: Moment
}
const GROUPS: Array<Filtred> = [{
    id: 1,    
    title: 'minute'
}, {
    id: 2,
    title: 'hour'
}, {
    id: 3,
    title: 'day'
}, {
    id: 4,
    title: 'week'
}, {
    id: 5,
    title: 'month'
}];

@Component({
  selector: 'order-book',
  styleUrls: [
      './style.scss'
  ],
  templateUrl: './template.html',
  providers: [
    OrderBookService,
    HistoryService
  ]
})
export class OrderBookComponent {
    data: any[];
    errorMessage: string;
    deph: any;
    plot: any;
    pair: boolean = false

    @ViewChild('chart', {static: false}) el:ElementRef;

    pairs = PAIRS.slice(1);
    groups = GROUPS;

    filter: Filter = {
        pair: this.pairs[0],
        group: GROUPS[0]
    }
    constructor(
        public appState: AppState,
        private orderBookService: OrderBookService,
        private route: ActivatedRoute,
        private historyService: HistoryService
    ) {}

    applyFilter(filter = {}) {
        this.filter = Object.assign(this.filter, filter);


        let groupName = 'month';
        let groupDelta = 2;
        const selectedIndex = this.groups.map(group => group.id)
            .indexOf(this.filter.group.id);
        if (this.groups[selectedIndex + 1]) {
            groupName = this.groups[selectedIndex + 1].title;
            groupDelta = 1;
        }

        this.filter.from = moment().subtract(
            groupDelta as DurationInputArg1, 
            groupName as DurationInputArg2
        ).utcOffset(0, true)
        this.filter.to = moment().utcOffset(0, true)

        const params = new HttpParams();
        const paramsObj = {
            pair: this.filter.pair.title,
            group: this.filter.group.title,
            from: this.filter.from,
            to: this.filter.to
        };
        Object.keys(paramsObj)
            .map(key => [key, paramsObj[key]])
            .forEach(([key, val]) => {
                params.set(key, val);
            });
        this.historyService
            .getList(params)
            .subscribe(
                info => {
                    this.deph = info;
                    if (this.plot) {
                        // Plotly.newPlot.apply(Plotly, this.getPlotlyArgs());
                    }
                },
                error => this.errorMessage = <any>error
            );
    }

    ngOnInit () {
        this.orderBookService
            .getWsData()
            .subscribe(
                data => this.data = data,
                error => this.errorMessage = <any>error
            );

        this.route.params.forEach((params: Params) => {
            this.applyFilter(params);
        });
    }
    unpack(col) {
        if (!this.deph) {
            return;
        }
        return this.deph.history.map(r => r[col]);
    }
    getPlotlyArgs() {
        const layout = {
              title: `Price for 
                ${this.filter.pair.title} 
              from ${this.filter.from.toISOString()}
              to ${this.filter.to.toISOString()}`.replace(/\s\s+/g, ' ')
        };
        const data = [{
            x: this.unpack('pub_date'),
            y: this.unpack('price'),
            type: 'scatter'
        }];
        return [
            this.el.nativeElement,
            data,
            layout
        ]
    }
    ngAfterViewInit() {
        // this.plot = Plotly.newPlot.apply(Plotly, this.getPlotlyArgs());
    }
}

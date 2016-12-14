import { Component, ViewEncapsulation } from '@angular/core';
import { AppState } from '../app.service';
import { Http, Response, Headers } from '@angular/http';

@Component({
    selector: 'order',
    styleUrls: [
        './style.css'
    ],
    templateUrl: './template.html'
})
export class OrderComponent {
    private dataUrl = '/api/order'
    private headers = new Headers({'Content-Type': 'application/json'});

    constructor(
        public appState: AppState,
        private http: Http
    ) {
    }
    onOrder() {
        this.http.post(this.dataUrl, JSON.stringify({
            price: 10,
            pair: 'btc_usd'
        }), {
            headers: this.headers
        }).subscribe(r => console.log(r))
    }
}

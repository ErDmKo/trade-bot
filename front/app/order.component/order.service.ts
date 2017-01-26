import { Injectable } from '@angular/core';
import { Http, Response, Headers, URLSearchParams } from '@angular/http';

@Injectable()
export class OrderService {
    private dataUrl = '/api/order';
    private headers = new Headers({'Content-Type': 'application/json'});

    constructor(
        private http: Http
    ) {
    }
    removeOrder(id) {
        let params: URLSearchParams = new URLSearchParams();
        params.set('id', id);

        return this.http.delete(this.dataUrl, {
                search: params
            })
            .map(this._toJSON)
    }
    getList() {
        return this.http.get(this.dataUrl)
            .map(this._toJSON)
    }
    onOrder(price, pair) {
        return this.http.post(this.dataUrl, JSON.stringify({
            price: price,
            pair: pair
        }), {
            headers: this.headers
        }).map(this._toJSON)
    }
    _toJSON(res: Response | Object) {
        let body: {
            orders?: any[]
        } = {};
        if (res instanceof Response) {
            body = res.json();
        } else {
            body = res;
        }
        return body;
    }
}

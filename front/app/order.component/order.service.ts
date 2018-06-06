import { Injectable } from '@angular/core';
import { Http, RequestOptionsArgs, Response, Headers, URLSearchParams } from '@angular/http';
import * as moment from 'moment';

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
            .map(this._toJSON.bind(this))
    }
    getById(id: string) {
        return this.http.get(`${this.dataUrl}/${id}`)
            .map(this._toJSONone.bind(this))
    }
    getList(params = {}) {
        const args: RequestOptionsArgs = { params }
        return this.http.get(this.dataUrl, args)
            .map(this._toJSON.bind(this))
    }
    onOrder(price, pair) {
        return this.http.post(this.dataUrl, JSON.stringify({
            price: price,
            pair: pair
        }), {
            headers: this.headers
        }).map(this._toJSON.bind(this))
    }
    _toJSONone(res: Response) {
        if (res instanceof Response) {
            return this._toModel(res.json());
        } else {
            return this._toModel(res);
        }
    }
    _toModel(jsonObj) {
        return Object.assign(jsonObj, {
            getDiff() {
                return moment(this.pub_date).fromNow(true);
            }
        });
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
        const out: {
            orders: any[]
        } = Object.assign(body, {
            orders: (body.orders || [])
                .map(this._toModel.bind(this))
        })
        return out;
    }
}


import {map} from 'rxjs/operators';
import { HttpClient, HttpHeaders, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import * as moment from 'moment';

@Injectable()
export class OrderService {
    private dataUrl = '/api/order';
    private headers = new HttpHeaders({'Content-Type': 'application/json'});

    constructor(
        private http: HttpClient
    ) {
    }
    removeOrder(id) {
        let params = new HttpParams();
        params.set('id', id);

        return this.http.delete(this.dataUrl, {
                params,
            }).pipe(
            map(this._toJSON.bind(this)))
    }
    getById(id: string) {
        return this.http.get(`${this.dataUrl}/${id}`).pipe(
            map(this._toJSONone.bind(this)))
    }
    getList(params: HttpParams) {
        return this.http.get(this.dataUrl, {
            params
        }).pipe(
            map(this._toJSON.bind(this)))
    }
    onOrder(price, pair) {
        return this.http.post(this.dataUrl, {
            price: price,
            pair: pair
        }, {
            headers: this.headers
        }).pipe(map(this._toJSON.bind(this)))
    }
    _toJSONone(res: HttpResponse<Record<string, any>>) {
        if (res instanceof HttpResponse) {
            return this._toModel(res.body);
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
    _toJSON(res: HttpResponse<Record<string, any>> | Object) {
        let body: {
            orders?: any[]
        } = {};
        if (res instanceof HttpResponse) {
            body = res.body;
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


import {map} from 'rxjs/operators';
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams, HttpResponse } from '@angular/common/http';

@Injectable()
export class HistoryService {
    private dataUrl = '/api/history';
    private headers = new HttpHeaders({
        'Content-Type': 'application/json'
    });
    constructor(
        private http: HttpClient
    ) {
    }
    getList(params: HttpParams) {
        return this.http.get(this.dataUrl, {
            params,
            headers: this.headers
        }).pipe(
        map(this._toJSON.bind(this)))
    }
    _toJSON(res: HttpResponse<Record<string, any>>) {
        let body: {
            history?: any[],
            meta?: any
        } = {};
        if (res instanceof HttpResponse) {
            body = res.body;
        }
        return body;
    }
}

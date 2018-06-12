import { Injectable } from '@angular/core';
import { 
    Http,
    RequestOptionsArgs,
    Response,
    Headers,
    URLSearchParams
} from '@angular/http';

@Injectable()
export class HistoryService {
    private dataUrl = '/api/history';
    private headers = new Headers({
        'Content-Type': 'application/json'
    });
    constructor(
        private http: Http
    ) {
    }
    getList(params = {}) {
        const args: RequestOptionsArgs = { params }
        return this.http.get(this.dataUrl, args)
            .map(this._toJSON.bind(this))
    }
    _toJSON(res: Response | Object) {
        let body: {
            history?: any[],
            meta?: any
        } = {};
        if (res instanceof Response) {
            body = res.json();
        }
        return body;
    }
}

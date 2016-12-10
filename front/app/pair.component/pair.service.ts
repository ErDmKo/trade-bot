import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import { Subject } from 'rxjs/Subject';
import { WebSocketSubject } from 'rxjs/observable/dom/WebSocketSubject'

@Injectable()
export class PairService {
    private url = "/api/pairs"
    private ws_url = "/api/ws_pairs"
    constructor (private http: Http) {}

    getPairs (): Observable<any[]> {
        return this.http.get(this.url)
                        .map(this.extractData)
                        .catch(this.handleError);
    }
    getWsPairs (): Observable<any[]> {
        return WebSocketSubject.create(
            this.getRelativeSocket(this.ws_url)
        ).map(this.extractData);
    }
    private extractData(res: Response | Object) {
        let body = {};
        if (res instanceof Response) {
            body = res.json();
        } else {
            body = res;
        }

        return Object.keys(body).map(key => ({ 
            name: key,
            params: Object.keys(body[key]).map(param => ({
                    name: param,
                    value: body[key][param]
                }))
        })) || {};
    }
    private handleError(error: Response | any) {
        let errMsg: string;
        if (error instanceof Response) {
            const body = error.json() || '';
            const err = body.error || JSON.stringify(body);
            errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
        } else {
            errMsg = error.message ? error.message : error.toString();
        }
        console.error(errMsg);
        return Observable.throw(errMsg);
    }
    private getRelativeSocket(path: String) {
        let loc: Location = window.location;
        let protocol: String = loc.protocol === "https:" ? "wss" : "ws";
        return `${protocol}://${loc.host}${path[0] == '/' ? '' : loc.pathname}${path}`
    }
}

import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import { Subject } from 'rxjs/Subject';
import { WebSocketSubject } from 'rxjs/observable/dom/WebSocketSubject'

@Injectable()
export class OrderBookService {
    private wsUrl = "/api/ws_order_book"

    constructor(){
    }

    getWsData (): Observable<any[]> {
        let sub: Subject<String> = WebSocketSubject.create(
            this.getRelativeSocket(this.wsUrl)
        )
        let obser = sub.map(this.extractData);
        sub.next('connect');
        return obser;
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
                    value: body[key][param].slice(0, 10)
                }))
        })) || {};
    }
    private getRelativeSocket(path: String) {
        let loc: Location = window.location;
        let protocol: String = loc.protocol === "https:" ? "wss" : "ws";
        return `${protocol}://${loc.host}${path[0] == '/' ? '' : loc.pathname}${path}`
    }
}

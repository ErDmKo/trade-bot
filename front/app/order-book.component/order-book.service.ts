import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import { Subject } from 'rxjs/Subject';
import { WebSocketSubject } from 'rxjs/observable/dom/WebSocketSubject'
import { SocketService } from '../common/socket.service'

@Injectable()
export class OrderBookService extends SocketService {
    protected wsUrl = "/api/ws_order_book"

    constructor(){
        super();
    }

    protected extractData(res: Response | Object) {
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
}

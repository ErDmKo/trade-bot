import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import { Subject } from 'rxjs/Subject';
import { WebSocketSubject } from 'rxjs/observable/dom/WebSocketSubject'
import { SocketService } from '../common/socket.service'

@Injectable()
export class BalanceService extends SocketService {
    protected wsUrl = "/api/ws_balance";

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
        return body;
    }
}

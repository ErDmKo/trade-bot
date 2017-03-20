import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import { Subject } from 'rxjs/Subject';
import { WebSocketSubject } from 'rxjs/observable/dom/WebSocketSubject'
import { SocketService } from '../common/socket.service'
import { IBalance } from '../common/api.interface'
import { IViewBalance} from '../common/view.interface'


@Injectable()
export class BalanceService extends SocketService {
    protected wsUrl = "/api/ws_balance";

    constructor(){
        super();
    }

    protected extractData(res: Response | Object) {
        let body: IBalance;
        if (res instanceof Response) {
            body = res.json();
        } else {
            body = res;
        }
        let out: IViewBalance = Object.assign({}, body);
        if (body.funds) {
            out.funds = Object.keys(body.funds).map((key)=>({
                'amount': body.funds[key],
                'name': key
            }));
        }
        return out;
    }
};

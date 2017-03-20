import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { SocketService } from '../common/socket.service'

@Injectable()
export class TradeLogService extends SocketService {
    protected wsUrl = "/api/ws_trade_log"

    constructor() {
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

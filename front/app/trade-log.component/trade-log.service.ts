import { HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { SocketService } from '../common/socket.service'

@Injectable()
export class TradeLogService extends SocketService {
    protected wsUrl = "/api/ws_trade_log"

    constructor() {
        super();
    }

    protected extractData(res: HttpResponse<Record<string, any>> | Object) {
        let body = {};
        if (res instanceof HttpResponse) {
            body = res.body;
        } else {
            body = res;
        }
        return body;
    }
}

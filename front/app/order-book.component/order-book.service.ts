import { HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { SocketService } from '../common/socket.service'

@Injectable()
export class OrderBookService extends SocketService {
    protected wsUrl = "/api/ws_order_book"

    constructor(){
        super();
    }

    protected extractData(res: HttpResponse<Record<string, any>> | Object) {
        let body = {};
        if (res instanceof HttpResponse) {
            body = res.body
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

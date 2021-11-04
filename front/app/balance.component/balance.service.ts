import { Injectable } from '@angular/core';
import { SocketService } from '../common/socket.service'
import { IBalance } from '../common/api.interface'
import { IViewBalance} from '../common/view.interface'
import { HttpResponse } from '@angular/common/http';


@Injectable({
    providedIn: 'root'
})
export class BalanceService extends SocketService<IViewBalance> {
    protected wsUrl = "/api/ws_balance";

    constructor(){
        super();
    }

    protected extractData(res: HttpResponse<Record<string, any>> | Object) {
        let body: IBalance;
        if (res instanceof HttpResponse) {
            body = res.body
        } else {
            body = res;
        }
        let out: IViewBalance = Object.assign({}, body) as any;
        if (body.funds) {
            out.funds = Object.keys(body.funds).map((key) => {
                const assetInfo = body.funds[key];
                return {
                    amount: assetInfo.amount,
                    currency: assetInfo.currency.toUpperCase(),
                    title: assetInfo.title,
                    name: key
                }
            });
        }
        return out;
    }
};

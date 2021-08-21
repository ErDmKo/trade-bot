
import {throwError as observableThrowError  } from 'rxjs';
import { HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { SocketService } from '../common/socket.service'

@Injectable()
export class PairService extends SocketService {
    protected wsUrl = "/api/ws_pairs"
    private pairList = [];

    constructor () {
        super();
    }

    public getPairs (): any[] {
        return this.pairList;
    }

    protected extractData(res: HttpResponse<Record<string, any>> | Object) {
        let body = {};
        if (res instanceof Response) {
            body = res.json();
        } else {
            body = res;
        }
        this.pairList = Object.keys(body);
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
            const err = JSON.stringify(body);
            errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
        } else {
            errMsg = error.message ? error.message : error.toString();
        }
        console.error(errMsg);
        return observableThrowError(errMsg);
    }
}

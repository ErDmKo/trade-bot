import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import { Observable } from 'rxjs/Observable';

@Injectable()
export class PairService {
    private url = "/api/pairs"
    constructor (private http: Http) {}

    getPairs (): Observable<any[]> {
        return this.http.get(this.url)
                        .map(this.extractData)
                        .catch(this.handleError);
    }
    private extractData(res: Response) {
       let body = res.json();
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
}

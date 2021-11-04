
import {map} from 'rxjs/operators';
import { Subject ,  Observable } from 'rxjs';
import { webSocket } from "rxjs/webSocket";
import { HttpResponse } from '@angular/common/http';

export abstract class SocketService<T> {
    sub: Subject<String>
    protected abstract wsUrl: string;

    public close() {
        this.sub.next('close')
    }
    protected observableSoket: Observable<T>

    public getWsData (): Observable<T> {
        if (this.observableSoket) {
            return this.observableSoket;
        }
        this.sub = webSocket(
            this.getRelativeSocket(this.wsUrl)
        )
        let obser = this.sub.pipe(map(this.extractData));
        this.sub.next('connect');
        this.observableSoket = obser;
        return obser;
    }

    protected getRelativeSocket(path: String) {
        let loc: Location = window.location;
        let protocol: String = loc.protocol === "https:" ? "wss" : "ws";
        return `${protocol}://${loc.host}${path[0] == '/' ? '' : loc.pathname}${path}`
    }
    protected abstract extractData(res: HttpResponse<string> | Object): T;
}

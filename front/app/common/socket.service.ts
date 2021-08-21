
import {map} from 'rxjs/operators';
import { Subject ,  Observable } from 'rxjs';
import { WebSocketSubject } from 'rxjs/observable/dom/WebSocketSubject'
import { HttpResponse } from '@angular/common/http';

export abstract class SocketService {
    sub: Subject<String>
    protected abstract wsUrl: string;

    public close() {
        this.sub.next('close')
    }

    public getWsData (): Observable<any[]> {
        this.sub = WebSocketSubject.create(
            this.getRelativeSocket(this.wsUrl)
        )
        let obser = this.sub.pipe(map(this.extractData));
        this.sub.next('connect');
        return obser;
    }

    protected getRelativeSocket(path: String) {
        let loc: Location = window.location;
        let protocol: String = loc.protocol === "https:" ? "wss" : "ws";
        return `${protocol}://${loc.host}${path[0] == '/' ? '' : loc.pathname}${path}`
    }
    protected abstract extractData(res: HttpResponse<string> | Object): any;
}

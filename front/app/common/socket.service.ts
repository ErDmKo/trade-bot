import { Subject } from 'rxjs/Subject';
import { Observable } from 'rxjs/Observable';
import { Response } from '@angular/http';
import { WebSocketSubject } from 'rxjs/observable/dom/WebSocketSubject'

export abstract class SocketService {

    protected abstract wsUrl: string;

    public getWsData (): Observable<any[]> {
        let sub: Subject<String> = WebSocketSubject.create(
            this.getRelativeSocket(this.wsUrl)
        )
        let obser = sub.map(this.extractData);
        sub.next('connect');
        return obser;
    }

    protected getRelativeSocket(path: String) {
        let loc: Location = window.location;
        let protocol: String = loc.protocol === "https:" ? "wss" : "ws";
        return `${protocol}://${loc.host}${path[0] == '/' ? '' : loc.pathname}${path}`
    }
    protected abstract extractData(res: Response | Object): Object;
}

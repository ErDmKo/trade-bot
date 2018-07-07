import { Component, ViewEncapsulation } from '@angular/core';
import 'rxjs/add/operator/filter';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { Title } from '@angular/platform-browser';

import { AppState } from './app.service';

import './rxjs-operators';

@Component({
    selector: 'app',
    encapsulation: ViewEncapsulation.None,
    templateUrl: './template.html',
    styleUrls: [
        './style.css'
    ],
})
export class AppComponent {

    constructor(
        public appState: AppState,
        private router: Router,
        private route: ActivatedRoute,
        private titleService: Title,
    ) {
    }

    ngOnInit() {
        this.router.events
            .filter(e => e instanceof NavigationEnd)
            .map(() => this.route)
            .map((route) => {
                while (route.firstChild) route = route.firstChild;
                return route
            })
            .filter(r => r.outlet == 'primary')
            .mergeMap(r => r.data)
            .subscribe(e => this.titleService.setTitle(e.title || '404'));
    }

}

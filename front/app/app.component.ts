import { Component, ViewEncapsulation } from '@angular/core';

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
    // angularclassLogo = 'assets/img/angularclass-avatar.png';
    name = 'Angular 2 Webpack Starter';
    url = 'https://twitter.com/AngularClass';

    constructor(
        public appState: AppState) {
    }

    ngOnInit() {
        console.log('Initial App State', this.appState.state);
    }

}

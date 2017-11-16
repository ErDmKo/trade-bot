import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { removeNgStyles, createNewHosts, createInputTransfer } from '@angularclass/hmr';
import { NgModule, ApplicationRef } from '@angular/core';

import { AppComponent } from './app.component';
import { PairComponent } from './pair.component';
import { IndexComponent } from './index.component';
import { BalanceComponent } from './balance.component';
import { OrderBookComponent } from './order-book.component';
import { TradeLogComponent } from './trade-log.component';
import { OrderComponent } from './order.component';
import { OrderDetailComponent } from './order-detail.component';
import { AppState, InternalStateType } from './app.service';
import { AppRoutingModule } from './app-routing.module';

import { ENV_PROVIDERS } from './environment';

type StoreType = {
    state: InternalStateType,
    restoreInputValues: () => void,
    disposeOldHosts: () => void
}
const APP_PROVIDERS = [
    AppState
];

@NgModule({
    bootstrap: [AppComponent],
    declarations: [
        AppComponent,
        OrderBookComponent,
        PairComponent,
        OrderComponent,
        BalanceComponent,
        TradeLogComponent,
        IndexComponent,
        OrderDetailComponent
    ],
    imports: [
        BrowserModule,
        FormsModule,
        HttpModule,
        BrowserAnimationsModule,
        AppRoutingModule
    ],
    providers: [
        ENV_PROVIDERS,
        APP_PROVIDERS
    ]
})
export class AppModule {
    constructor(public appRef: ApplicationRef, public appState: AppState) {}
    hmrOnInit(store: StoreType) {
        if (!store || !store.state) return;
        console.log('HMR store', JSON.stringify(store, null, 2));
        // set state
        this.appState._state = store.state;
        // set input values
        if ('restoreInputValues' in store) {
            let restoreInputValues = store.restoreInputValues;
            setTimeout(restoreInputValues);
        }

        this.appRef.tick();
        delete store.state;
        delete store.restoreInputValues;
    }

    hmrOnDestroy(store: StoreType) {
        const cmpLocation = this.appRef.components.map(cmp => cmp.location.nativeElement);
        // save state
        const state = this.appState._state;
        store.state = state;
        // recreate root elements
        store.disposeOldHosts = createNewHosts(cmpLocation);
        // save input values
        store.restoreInputValues  = createInputTransfer();
        // remove styles
        removeNgStyles();
    }

    hmrAfterDestroy(store: StoreType) {
        // display new elements
        store.disposeOldHosts();
        delete store.disposeOldHosts;
    }
}

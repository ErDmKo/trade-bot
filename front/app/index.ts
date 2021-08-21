import { BrowserModule, Title } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import { PairComponent } from './pair.component';
import { IndexComponent } from './index.component';
import { BalanceComponent } from './balance.component';
import { OrderBookComponent } from './order-book.component';
import { TradeLogComponent } from './trade-log.component';
import { OrderComponent } from './order.component';
import { OrderDetailComponent } from './order-detail.component';
import { AppState } from './app.service';
import { AppRoutingModule } from './app-routing.module';

import { ENV_PROVIDERS } from './environment';
import { HttpClientModule } from '@angular/common/http';

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
        HttpClientModule,
        BrowserAnimationsModule,
        AppRoutingModule,
        FormsModule,
    ],
    providers: [
        Title,
        ENV_PROVIDERS,
        APP_PROVIDERS
    ]
})
export class AppModule {}

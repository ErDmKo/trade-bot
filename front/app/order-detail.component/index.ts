import { Component } from '@angular/core';
import { OrderService } from '../order.component/order.service';
import { ActivatedRoute, Params } from '@angular/router';

@Component({
    selector: 'order-detail',
    styleUrls: [
        './style.scss'
    ],
    templateUrl: './template.html',
    providers: [
        OrderService
    ]
})
export class OrderDetailComponent {
    order: any;
    ngOnInit(): void {
        this.route.params.forEach((params: Params) => {
            this.getOrder(params.id);
        })
    }
    getOrder(id) {
        this.orderService.getById(id)
            .subscribe(info => {
                this.order = info
            })
    }
    constructor(
        private orderService: OrderService,
        private route: ActivatedRoute
    ) {}
}

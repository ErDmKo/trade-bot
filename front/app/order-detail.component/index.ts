import { Component } from '@angular/core';
import { OrderService } from '../order.component/order.service';
import { ActivatedRoute } from '@angular/router';

@Component({
    selector: 'order-detail',
    styleUrls: [
        './style.css'
    ],
    templateUrl: './template.html',
    providers: [
        OrderService
    ]
})
export class OrderDetailComponent {
    private order: any;
    ngOnInit(): void {
          this.getOrder();
    }
    getOrder() {
        const id = this.route.snapshot.paramMap.get('id');
        this.orderService.getById(id)
            .subscribe(info => {
                this.order = JSON.stringify(info)
            })
    }
    constructor(
        private orderService: OrderService,
        private route: ActivatedRoute
    ) {}
}

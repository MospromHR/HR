import {Component, input} from '@angular/core';

@Component({
    selector: 'profile-list-item',
    imports: [],
    templateUrl: './list-item.component.html',
    styleUrl: './list-item.component.less'
})
export class ListItemComponent {
    header = input.required<string>();
    viewQuantity = input.required<number>();
    responsesQuantity = input.required<number>();
    conversionPercentage = input.required<number>();
}

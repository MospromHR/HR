import {Component, input, signal} from '@angular/core';
import {ButtonComponent} from "../../ui/button/button.component";

@Component({
    selector: 'profile-list',
    imports: [
        ButtonComponent
    ],
    templateUrl: './list.component.html',
    styleUrl: './list.component.less'
})
export class ListComponent {
    key = input.required<string>();
    list = signal([])
}

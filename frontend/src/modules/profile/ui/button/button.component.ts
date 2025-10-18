import {Component, input} from '@angular/core';

@Component({
    selector: 'profile-button',
    imports: [],
    templateUrl: './button.component.html',
    styleUrl: './button.component.less'
})
export class ButtonComponent {
    title = input.required<string>();
    isActive = input(false);
}

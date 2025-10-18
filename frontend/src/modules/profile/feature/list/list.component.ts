import {Component, input, signal} from '@angular/core';
import {ButtonComponent} from "../../ui/button/button.component";
import {ListItemComponent} from "../../ui/list-item/list-item.component";
import {FeatureToggleDirective} from "../../../../utils/feature-toggle.directive";
import {RouterLink} from "@angular/router";

@Component({
    selector: 'profile-list',
    imports: [
        ButtonComponent,
        ListItemComponent,
        FeatureToggleDirective,
        RouterLink
    ],
    templateUrl: './list.component.html',
    styleUrl: './list.component.less'
})
export class ListComponent {
    key = input.required<string>();
    list = signal<{ id: string, title: string, views: number, responses: number, conversion: number }[]>([
        // {
        //     id: 1,
        //     title: 'Химик-аналитик (Группа физико-химических методов)',
        //     views: 562,
        //     responses: 34,
        //     conversion: 28
        // },
        // {
        //     id: 2,
        //     title: 'Химик-аналитик',
        //     views: 562,
        //     responses: 34,
        //     conversion: 28
        // },
    ])
}

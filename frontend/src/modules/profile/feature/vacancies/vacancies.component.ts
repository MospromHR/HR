import {Component, signal} from '@angular/core';
import {ButtonComponent} from "../../ui/button/button.component";
import {ListComponent} from "../list/list.component";
import {RouterLink} from "@angular/router";
import {FeatureToggleDirective} from "../../../../utils/feature-toggle.directive";

@Component({
    selector: 'profile-vacancies',
    imports: [
        ButtonComponent,
        ListComponent,
        ListComponent,
        RouterLink,
        FeatureToggleDirective
    ],
    templateUrl: './vacancies.component.html',
    styleUrl: './vacancies.component.less'
})
export class VacanciesComponent {
    selectedKey = signal('')
}

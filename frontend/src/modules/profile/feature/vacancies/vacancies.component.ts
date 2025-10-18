import {Component, signal} from '@angular/core';
import {ButtonComponent} from "../../ui/button/button.component";
import {ListComponent} from "../list/list.component";

@Component({
    selector: 'profile-vacancies',
    imports: [
        ButtonComponent,
        ListComponent,
        ListComponent
    ],
    templateUrl: './vacancies.component.html',
    styleUrl: './vacancies.component.less'
})
export class VacanciesComponent {
    selectedKey = signal('')
}

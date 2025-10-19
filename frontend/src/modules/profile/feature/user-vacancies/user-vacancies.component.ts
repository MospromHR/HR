import {Component, signal} from '@angular/core';
import {ButtonComponent} from "../../ui/button/button.component";
import {UserListComponent} from "./list/user-list.component";

@Component({
    selector: 'profile-user-vacancies',
    imports: [
        ButtonComponent,
        UserListComponent
    ],
    templateUrl: './user-vacancies.component.html',
    styleUrl: './user-vacancies.component.less'
})
export class UserVacanciesComponent {
    selectedKey = signal('')
}

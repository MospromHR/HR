import {Component} from '@angular/core';
import {ButtonComponent} from "../../ui/button/button.component";
import {TableComponent} from "../table/table.component";
import {RouterLink} from "@angular/router";

@Component({
    selector: 'profile-internship-applications',
    imports: [
        ButtonComponent,
        TableComponent,
        RouterLink
    ],
    templateUrl: './internship-applications.component.html',
    styleUrl: './internship-applications.component.less'
})
export class InternshipApplicationsComponent {

}

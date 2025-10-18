import {Component} from '@angular/core';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {TuiInputModule} from "@taiga-ui/legacy";
import {Router} from "@angular/router";

@Component({
    selector: 'profile-create-vacancy',
    imports: [
        ReactiveFormsModule,
        TuiInputModule
    ],
    templateUrl: './create-vacancy.component.html',
    styleUrl: './create-vacancy.component.less'
})
export class CreateVacancyComponent {
    form = new FormGroup({
        vacancyName: new FormControl('', [Validators.required]),
        logo: new FormControl(''),
        companyName: new FormControl('', [Validators.required]),
        site: new FormControl('', [Validators.required]),
        speciality: new FormControl('', [Validators.required]),

        responsibilities: new FormControl('', [Validators.required]),

        requirements: new FormControl('', [Validators.required]),

        terms: new FormControl('',),
        workSchedule: new FormControl('',),
        workPlace: new FormControl('',),
        map: new FormControl('',),
        probation: new FormControl('',),
        salary: new FormControl('',),
        additionally: new FormControl('',),
        aboutCompany: new FormControl('',),
        companyLink: new FormControl('',),
        task: new FormControl('',),
    })

    constructor(private router: Router) {
    }

    send():void{
        this.router.navigate(['/profile']).then();
    }
}

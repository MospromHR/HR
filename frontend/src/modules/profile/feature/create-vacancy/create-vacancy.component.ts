import {Component, DestroyRef} from '@angular/core';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {TuiInputModule} from "@taiga-ui/legacy";
import {Router} from "@angular/router";
import {VacancyService} from "../../data-access/vacancy.service";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";


interface FormData {
    vacancyName: string,
    logo: string
    companyName: string,
    site: string,
    speciality: string,
    responsibilities: string,
    requirements: string,
    terms: string,
    workSchedule: string,
    workPlace: string,
    map: string,
    probation: string,
    salary: string,
    additionally: string,
    aboutCompany: string,
    companyLink: string,
    task: string,
}

@Component({
    selector: 'profile-create-vacancy',
    imports: [
        ReactiveFormsModule,
        TuiInputModule
    ],
    providers: [VacancyService],
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

    constructor(private router: Router,
                private vacancyService: VacancyService,
                private destroyRef: DestroyRef) {
    }

    send(): void {
        const {
            vacancyName,
            speciality,
            responsibilities,
            requirements,
            terms,
            workSchedule,
            workPlace,
            map,
            probation,
            salary,
            additionally,
            task
        } = this.form.value as FormData;
        const data = {
            vacancyName,
            speciality,
            responsibilities,
            requirements,
            terms,
            workSchedule,
            workPlace,
            map,
            probation,
            salary,
            additionally,
            task
        }
        this.vacancyService.postCompanyVacancies(data).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(
            ()=>{
                this.router.navigate(['/profile/vacancies']).then();
            }
        )

    }
}

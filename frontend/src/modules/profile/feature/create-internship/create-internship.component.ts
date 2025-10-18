import {Component, DestroyRef} from '@angular/core';
import {Router} from '@angular/router';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators} from "@angular/forms";
import {
    TuiInputDateRangeModule,
    TuiInputModule,
    TuiInputNumberModule,
    TuiTextfieldControllerModule
} from "@taiga-ui/legacy";
import {TuiDay, TuiDayRange} from "@taiga-ui/cdk";
import {InternshipService} from "../../data-access/internship.service";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";

interface FormData {
    speciality: string,
    quantity: number,
    course: number,
    type: string,
    description: string,
    date: TuiDayRange,
}

@Component({
    selector: 'profile-create-internship',
    imports: [
        FormsModule,
        ReactiveFormsModule,
        TuiInputModule,
        TuiInputNumberModule,
        TuiInputDateRangeModule,
        TuiTextfieldControllerModule
    ],
    providers: [InternshipService],
    templateUrl: './create-internship.component.html',
    styleUrl: './create-internship.component.less'
})
export class CreateInternshipComponent {
    form = new FormGroup({
        speciality: new FormControl('', [Validators.required]),
        quantity: new FormControl(1, [Validators.required]),
        course: new FormControl(1, [Validators.required]),
        date: new FormControl<TuiDayRange | null>(null, [Validators.required]),
        type: new FormControl('', [Validators.required]),
        description: new FormControl('', ),
    });

    constructor(private router: Router,
                private internshipService: InternshipService,
                private destroyRef: DestroyRef) {
    }

    send(): void {
        const {speciality, quantity, course, date, type, description,} = this.form.value as FormData;
        if (!date) {
            return;
        }
        const data = {
            title: speciality,
            speciality_code: speciality,
            start_date: this.formatDate(date.from),
            end_date: this.formatDate(date.to),
            capacity: quantity,
            course: course,
            type: type,
            description: description,
        }
        this.internshipService.postEducationInternships(data).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
            this.router.navigate(['profile/internship-applications']).then();
        });

    }

    private formatDate(tuiDay: TuiDay): string {
        const year = tuiDay.year;
        const month = (tuiDay.month + 1).toString().padStart(2, '0');
        const day = tuiDay.day.toString().padStart(2, '0');

        return `${year}-${month}-${day}`;
    }
}

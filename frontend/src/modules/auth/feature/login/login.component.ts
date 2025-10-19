import {Component, DestroyRef,} from '@angular/core';
import {TuiInputModule, TuiInputPasswordModule} from '@taiga-ui/legacy';
import {Router} from '@angular/router';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {AuthService} from "../../data-access/auth.service";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";
import {tap} from "rxjs";

@Component({
    selector: 'auth-login',
    providers: [AuthService],
    imports: [
        TuiInputModule,
        TuiInputPasswordModule,
        ReactiveFormsModule,
    ],
    templateUrl: './login.component.html',
    styleUrl: './login.component.less'
})
export class LoginComponent {
    authForm = new FormGroup({
        login: new FormControl('', [Validators.required, Validators.minLength(3), Validators.email]),
        password: new FormControl('', [Validators.required, Validators.minLength(3)])
    })

    constructor(private router: Router,
                private authService: AuthService,
                private destroyRef: DestroyRef) {
    }

    goToLogin(): void {
        const {login, password} = this.authForm.getRawValue();
        if (login && password) {
            this.authService.login(login, password).pipe(tap((role) => {
                if (role === 'company') {
                    this.router.navigate(['/profile/vacancies']).then();
                } else if (role === 'education') {
                    this.router.navigate(['/profile/internship-applications']).then();
                } else if (role === 'applicant') {
                    this.router.navigate(['/profile/list']).then();
                }
            }),takeUntilDestroyed(this.destroyRef)).subscribe();

        }

    }

    goToRegister(): void {
        this.router.navigate(['/auth'], {}).then();
    }
}

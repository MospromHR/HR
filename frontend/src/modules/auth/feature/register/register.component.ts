import {Component, DestroyRef, signal,} from '@angular/core';
import {TuiInputModule, TuiInputPasswordModule} from '@taiga-ui/legacy';
import {ActivatedRoute, Router} from '@angular/router';
import {
    AbstractControl,
    FormControl,
    FormGroup,
    ReactiveFormsModule,
    ValidationErrors,
    Validators
} from "@angular/forms";
import {AuthService} from "../../data-access/auth.service";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";
import {Role} from "../../../../data-access/api.interfaces";


function passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const secPassword = control.get('secPassword');

    if (!password || !secPassword) {
        return null;
    }

    return password.value === secPassword.value ? null : {passwordMismatch: true};
}

@Component({
    selector: 'auth-register',
    providers: [AuthService],
    imports: [
        TuiInputModule,
        TuiInputPasswordModule,
        ReactiveFormsModule,
    ],
    templateUrl: './register.component.html',
    styleUrl: './register.component.less'
})
export class RegisterComponent {
    role = signal<Role | undefined>(undefined)
    form = new FormGroup({
        login: new FormControl('', [Validators.required, Validators.minLength(3), Validators.email]),
        password: new FormControl('', [Validators.required, Validators.minLength(3)]),
        secPassword: new FormControl('', [Validators.required, Validators.minLength(3)]),
    }, {validators: passwordMatchValidator})

    constructor(private router: Router,
                private authService: AuthService,
                private destroyRef: DestroyRef,
                private route: ActivatedRoute) {
        this.route.queryParams.subscribe(params => {
            const role = params['role'];
            this.role.set(role);
        })
    }

    goToLogin(): void {
        const role = this.role() ?? 'applicant';

        const {login, password} = this.form.getRawValue();
        if (login && password) {
            this.authService.register(login, password, role).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
                this.router.navigate(['/auth/login'], {}).then();
            });

        }

    }

    goToRegister(): void {
        this.router.navigate(['/auth'], {}).then();
    }
}

import {Component, DestroyRef,} from '@angular/core';
import {TuiInputModule, TuiInputPasswordModule} from '@taiga-ui/legacy';
import {Router} from '@angular/router';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {AuthService} from "../../data-access/auth.service";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";

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
        login: new FormControl('', [Validators.required, Validators.minLength(3),  Validators.email]),
        password: new FormControl('', [Validators.required, Validators.minLength(3)])
    })

    constructor(private router: Router,
                private authService: AuthService,
                private destroyRef: DestroyRef) {
    }

    goToLogin(): void {
        const {login, password} = this.authForm.getRawValue();
        if (login && password) {
            this.authService.login(login, password).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
                this.router.navigate(['/profile'], {}).then();
            });

        }

    }

    goToRegister(): void {
        this.router.navigate(['/auth'], {}).then();
    }
}

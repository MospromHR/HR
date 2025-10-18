import {Component,} from '@angular/core';
import {TuiInputModule, TuiInputPasswordModule} from '@taiga-ui/legacy';
import {Router} from '@angular/router';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";

@Component({
    selector: 'auth-login',
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
        login: new FormControl('', [Validators.required]),
        password: new FormControl('', [Validators.required])
    })

    constructor(private router: Router) {
    }

    goToLogin(): void {
        this.router.navigate(['/profile'], {}).then();
    }

    goToRegister(): void {
        this.router.navigate(['/auth'], {}).then();
    }
}

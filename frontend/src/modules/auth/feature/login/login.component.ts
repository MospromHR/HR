import {Component,} from '@angular/core';
import {TuiInputModule, TuiInputPasswordModule} from '@taiga-ui/legacy';
import {Router} from '@angular/router';

@Component({
  selector: 'auth-login',
  imports: [
    TuiInputModule,
    TuiInputPasswordModule,
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.less'
})
export class LoginComponent {
  constructor(private router: Router) {
  }
  goToLogin(): void {

  }

  goToRegister(): void {
    this.router.navigate(['/auth/register'], {
    }).then();
  }
}

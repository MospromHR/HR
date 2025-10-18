import {Component, signal} from '@angular/core';
import {RoleItemComponent} from '../../ui/role-item/role-item.component';
import {Router} from '@angular/router';

type Role = 'company' | 'candidate' | 'university';

@Component({
  selector: 'auth-role',
  imports: [
    RoleItemComponent
  ],
  templateUrl: './role.component.html',
  styleUrl: './role.component.less'
})
export class RoleComponent {
  selectedRole = signal<Role>('candidate')

  selectRole(role: Role) {
    this.selectedRole.set(role);
  }

  constructor(private router: Router) {
  }

  goToLogin(): void {
    this.router.navigate(['/auth/login'], {
      queryParams: { role: this.selectedRole() }
    }).then();
  }

  goToRegister(): void {
    this.router.navigate(['/auth/register'], {
      queryParams: { role: this.selectedRole() }
    }).then();
  }
}

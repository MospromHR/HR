import {Component, signal} from '@angular/core';
import {RoleItemComponent} from '../../ui/role-item/role-item.component';
import {Router} from '@angular/router';
import {Role} from "../../../../data-access/api.interfaces";


@Component({
    selector: 'auth-role',
    imports: [
        RoleItemComponent
    ],
    templateUrl: './role.component.html',
    styleUrl: './role.component.less'
})
export class RoleComponent {
    selectedRole = signal<Role>('applicant')

    selectRole(role: Role) {
        this.selectedRole.set(role);
    }

    constructor(private router: Router) {
    }

    goToLogin(): void {
        this.router.navigate(['/auth/login']).then();
    }

    goToRegister(): void {
        this.router.navigate(['/auth/register'], {
            queryParams: {role: this.selectedRole()}
        }).then();
    }
}

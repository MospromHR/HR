import {Component} from '@angular/core';
import {Router, RouterLink} from "@angular/router";
import {AuthService} from "../../../auth/data-access/auth.service";

@Component({
    selector: 'profile-nav',
    imports: [
        RouterLink
    ],
    templateUrl: './nav.component.html',
    styleUrl: './nav.component.less'
})
export class NavComponent {

    constructor(private  authService: AuthService,
                private router: Router ) {
    }

    logout(): void {
        this.authService.logout();
        this.router.navigate(['/auth']).then();

    }
}

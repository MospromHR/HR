import {Component} from '@angular/core';
import {Router, RouterLink} from "@angular/router";
import {AuthService} from "../../../auth/data-access/auth.service";
import {FeatureToggleDirective} from "../../../../utils/feature-toggle.directive";

@Component({
    selector: 'profile-nav',
    imports: [
        RouterLink,
        FeatureToggleDirective
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

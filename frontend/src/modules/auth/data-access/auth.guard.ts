import {inject} from '@angular/core';
import {CanActivateFn, Router} from '@angular/router';
import {AuthService} from './auth.service';
import {tap} from 'rxjs';
import {MeStore} from "../../profile/data-access/me.store";

export const authGuard: CanActivateFn = () => {
    const authService = inject(AuthService);
    const meStore = inject(MeStore);
    const router = inject(Router);
    if (authService.isAuthenticated()) {
        meStore.loadProfile();
        return true;
    } else {
        router.navigate(['/auth']).then();
        return false;
    }
};

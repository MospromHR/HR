import {inject} from '@angular/core';
import {ActivatedRouteSnapshot, CanActivateFn, Router} from '@angular/router';
import {AuthService} from './auth.service';
import {tap} from 'rxjs';
import {MeStore} from "../../profile/data-access/me.store";
import {FeatureToggleService} from "../../../utils/feature-toggle.service";

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

export const smartRedirectGuard = () => {
    // Проверяем доступность маршрутов через те же гварды
    const toggleService =  inject(FeatureToggleService)
    const educationAccess = toggleService.isEducation();
    const companyAccess = toggleService.isCompany();

    if (educationAccess) {
        return '/profile/internship-applications';
    } else if (companyAccess) {
        return '/profile/vacancies';
    } else {
        // Fallback - можно перенаправить на общую страницу профиля
        return '/profile/vacancies';
    }
};

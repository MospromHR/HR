import {Routes} from '@angular/router';
import {authGuard, smartRedirectGuard} from '../modules/auth/data-access/auth.guard';
import {CreateVacancyComponent} from "../modules/profile/feature/create-vacancy/create-vacancy.component";
import {
    InternshipApplicationsComponent
} from "../modules/profile/feature/internship-applications/internship-applications.component";
import {featureToggleGuard} from "../modules/auth/data-access/feature-toggle.guard";
import {UserVacanciesComponent} from "../modules/profile/feature/user-vacancies/user-vacancies.component";
import {AccountComponent} from "../modules/profile/feature/account/account.component";

export const routes: Routes = [
    {
        path: '',
        pathMatch: 'full',
        redirectTo: 'auth'
    },
    {
        path: 'auth',
        loadComponent: () => import('../modules/auth/shell/auth/auth.component').then(m => m.AuthComponent),
        //todo перенести либу auth
        children: [
            {
                path: '',
                loadComponent: () => import('../modules/auth/feature/role/role.component').then(m => m.RoleComponent),
            },
            {
                path: 'login',
                loadComponent: () => import('../modules/auth/feature/login/login.component').then(m => m.LoginComponent)
            },
            {
                path: 'register',
                loadComponent: () => import('../modules/auth/feature/register/register.component').then(m => m.RegisterComponent)
            }
        ]
    },
    {
        path: 'profile',
        loadComponent: () => import('../modules/profile/shell/profile/profile.component').then(m => m.ProfileComponent),
        canActivate: [authGuard],
        children: [
            {
                path: '',
                redirectTo: 'internship-applications',
                pathMatch: 'full'
            },
            {
                path: 'vacancies',
                loadComponent: () => import('../modules/profile/feature/vacancies/vacancies.component').then(m => m.VacanciesComponent),
                // canActivate: [featureToggleGuard('company')],
            },

            {
                path: 'account',
                loadComponent: () => import('../modules/profile/feature/account/account.component').then(m => m.AccountComponent),
                // canActivate: [featureToggleGuard('company')],
            },
            {
                path: 'list',
                loadComponent: () => import('../modules/profile/feature/user-vacancies/user-vacancies.component').then(m => m.UserVacanciesComponent),
            },

            {
                path: 'create-vacancy',
                loadComponent: () => import('../modules/profile/feature/create-vacancy/create-vacancy.component').then(m => m.CreateVacancyComponent),
            },
            {
                path: 'internship-applications',
                loadComponent: () => import('../modules/profile/feature/internship-applications/internship-applications.component').then(m => m.InternshipApplicationsComponent),
                // canActivate: [featureToggleGuard('education')],
            },
            {
                path: 'create-internship',
                loadComponent: () => import('../modules/profile/feature/create-internship/create-internship.component').then(m => m.CreateInternshipComponent),
            },
        ],
    }
];

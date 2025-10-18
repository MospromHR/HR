import {Routes} from '@angular/router';
import {authGuard} from '../modules/auth/data-access/auth.guard';

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
        //todo перенести либу auth
        children: [
            {
                path: '',
                loadComponent: () => import('../modules/profile/feature/vacancies/vacancies.component').then(m => m.VacanciesComponent),
            },
        ],
    }
];

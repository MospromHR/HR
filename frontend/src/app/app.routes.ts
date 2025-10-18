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
    // canActivate: [authGuard],
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
];

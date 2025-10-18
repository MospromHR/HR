import {inject} from '@angular/core';
import {CanActivateFn, Router} from '@angular/router';
import {AuthService} from './auth.service';
import {tap} from 'rxjs';

export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);
  return authService.authorized$.pipe(
    tap((isAuthorized) => {
      if (!isAuthorized) {
        router.navigate(['/auth-flow']).then();
      }
    }),
  );
};

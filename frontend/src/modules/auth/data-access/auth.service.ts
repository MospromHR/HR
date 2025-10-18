import {Injectable} from '@angular/core';
import {Observable, of} from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AuthService  {
  readonly authorized$: Observable<boolean> = of(true);
}

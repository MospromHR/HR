import {Injectable, signal} from '@angular/core';
import {BehaviorSubject, map, Observable, tap} from 'rxjs';
import {HttpClient} from "@angular/common/http";
import {Role} from "../../../data-access/api.interfaces";
import {http} from "../../../data-access/api.const";

interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}



@Injectable({
    providedIn: 'root',
})
export class AuthService {
    isAuth = signal(false);

    private accessToken = new BehaviorSubject<string | null>(null);
    private readonly TOKEN_KEY = 'access_token';
    private readonly REFRESH_TOKEN_KEY = 'refresh_token';


    constructor(private httpClient: HttpClient) {
        const savedToken = localStorage.getItem(this.TOKEN_KEY);
        if (savedToken) {
            this.accessToken.next(savedToken);
        }
    }

    login(email: string, password: string): Observable<void> {
        return this.httpClient.post<AuthResponse>(`${http}/api/v1/auth/login`, {
            email,
            password
        }).pipe(map((response) => {
            this.setTokens(response)
        }))
    }

    register(email: string, password: string, role: Role): Observable<void> {
        return this.httpClient.post<AuthResponse>(`${http}/api/v1/auth/register`, {
            email,
            role,
            password
        }).pipe(map((response) => {
            this.setTokens(response)
        }))
    }

    getAccessToken(): string | null {
        const token = localStorage.getItem(this.TOKEN_KEY);
        this.isAuth.set(!!token)
        return token
    }

    getRefreshToken(): string | null {
        return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    }

    isAuthenticated(): boolean {
        return !!this.getAccessToken();
    }

    logout(): void {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
        this.accessToken.next(null);
    }

    refreshToken(): Observable<AuthResponse> {
        const refreshToken = this.getRefreshToken();
        return this.httpClient.post<AuthResponse>(`${http}/api/v1/auth/refresh`, {refresh_token: refreshToken})
            .pipe(
                tap(response => this.setTokens(response))
            );
    }

    private setTokens(response: AuthResponse): void {
        localStorage.setItem(this.TOKEN_KEY, response.access_token);
        localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refresh_token);
        this.accessToken.next(response.access_token);
    }


}

import {Injectable} from '@angular/core';
import {BehaviorSubject, map, Observable, of, tap} from 'rxjs';
import {HttpClient} from "@angular/common/http";

interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

const http = 'https://hackathon.silkslime.ru'

@Injectable({
    providedIn: 'root',
})
export class AuthService {
    private accessToken = new BehaviorSubject<string | null>(null);
    private readonly TOKEN_KEY = 'access_token';
    private readonly REFRESH_TOKEN_KEY = 'refresh_token';
    readonly authorized$: Observable<boolean> = of(true);

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

    getAccessToken(): string | null {
        return localStorage.getItem(this.TOKEN_KEY);
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

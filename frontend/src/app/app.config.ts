import {provideEventPlugins} from "@taiga-ui/event-plugins";
import {provideAnimations} from "@angular/platform-browser/animations";
import {
    ApplicationConfig,
    importProvidersFrom,
    provideBrowserGlobalErrorListeners,
    provideZoneChangeDetection
} from '@angular/core';
import {provideRouter} from '@angular/router';

import {routes} from './app.routes';
import {HttpClientModule, provideHttpClient, withInterceptors} from '@angular/common/http';
import {authInterceptor} from "../modules/auth/data-access/auth.inteceptor";
import {TUI_LANGUAGE, TUI_RUSSIAN_LANGUAGE} from "@taiga-ui/i18n";
import {of} from "rxjs";

export const appConfig: ApplicationConfig = {
    providers: [
        provideAnimations(),
        provideBrowserGlobalErrorListeners(),
        provideZoneChangeDetection({eventCoalescing: true}),
        provideRouter(routes),
        importProvidersFrom(HttpClientModule),
        {
            provide: TUI_LANGUAGE,
            useValue: of(TUI_RUSSIAN_LANGUAGE),
        },
        provideHttpClient(
            withInterceptors([authInterceptor]) // ← Регистрируем интерцептор
        ),
        provideEventPlugins()
    ]
};

import {computed, Injectable} from "@angular/core";
import {MeStore} from "../modules/profile/data-access/me.store";
import {FeatureToggleKey} from "./feature-toggle-key.interfaces";

@Injectable({
    providedIn: 'root',
})
export class FeatureToggleService {
    isApplicant = computed(() => this.meStore.me()?.role === 'applicant');
    isCompany = computed(() => this.meStore.me()?.role === 'company');
    isEducation = computed(() => this.meStore.me()?.role === 'education');


    constructor(private meStore: MeStore) {
    }

    isFeatureEnabled(key: FeatureToggleKey): boolean {
        switch (key) {
            case 'applicant':
                return this.isApplicant();
            case 'company':
                return this.isCompany();
            case 'education':
                return this.isEducation();
            default:
                return false;
        }
    }
}
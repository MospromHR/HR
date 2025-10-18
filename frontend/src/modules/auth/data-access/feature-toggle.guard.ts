import {inject} from '@angular/core';
import {CanActivateFn} from '@angular/router';
import {FeatureToggleKey} from "../../../utils/feature-toggle-key.interfaces";
import {FeatureToggleService} from "../../../utils/feature-toggle.service";


export function featureToggleGuard(featureKey: FeatureToggleKey): CanActivateFn {
    return () => {
        return inject(FeatureToggleService).isFeatureEnabled(featureKey);

    };
}

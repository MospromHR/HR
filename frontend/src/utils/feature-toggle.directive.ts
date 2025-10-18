import {Directive, effect, input, TemplateRef, ViewContainerRef} from '@angular/core';
import {FeatureToggleKey} from "./feature-toggle-key.interfaces";
import {FeatureToggleService} from "./feature-toggle.service";

@Directive({
    selector: '[roleFeatureToggle]',
})
export class FeatureToggleDirective {
    roleFeatureToggle = input.required<FeatureToggleKey>();

    constructor(
        private featureToggleService: FeatureToggleService,
        private viewContainer: ViewContainerRef,
        private templateRef: TemplateRef<unknown>,
    ) {
        effect(() => {
            this.updateView();
        });
    }

    private updateView(): void {
        const key = this.roleFeatureToggle();
        this.viewContainer.clear();

        if (this.featureToggleService.isFeatureEnabled(key)) {
            this.viewContainer.createEmbeddedView(this.templateRef);
        }
    }
}

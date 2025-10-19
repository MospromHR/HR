import {Component, DestroyRef, OnInit} from '@angular/core';
import {AccountService} from "./account.service";
import {TuiInputModule} from "@taiga-ui/legacy";
import {FormControl, ReactiveFormsModule} from "@angular/forms";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";

@Component({
    selector: 'profile-account',
    imports: [
        TuiInputModule,
        ReactiveFormsModule
    ],
    templateUrl: './account.component.html',
    styleUrl: './account.component.less'
})
export class AccountComponent implements OnInit {
    codeControl = new FormControl('');

    constructor(private accountService: AccountService,
                private destroy: DestroyRef) {
    }

    ngOnInit(): void {
    }

    send(){
        const value = this.codeControl.value
        if(value){
            this.accountService.setCode(value).pipe(takeUntilDestroyed(this.destroy)).subscribe();
        }
    }

}

import {Component, DestroyRef, input, OnInit, signal} from '@angular/core';
import {ListItemComponent} from "../../../ui/list-item/list-item.component";
import {Vacancy} from "./interfaces";
import {VacancyService} from "../../../data-access/vacancy.service";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";
import {tap} from "rxjs";

@Component({
    selector: 'profile-user-list',
    imports: [
        ListItemComponent,
    ],
    providers: [VacancyService],
    templateUrl: './user-list.component.html',
    styleUrl: './user-list.component.less'
})
export class UserListComponent implements OnInit{
    key = input.required<string>();
    list = signal<Vacancy[]>([])

    constructor(private vacancyService: VacancyService,
                private destroy: DestroyRef) {
    }

    ngOnInit(): void {
        this.vacancyService.getShortVacancies().pipe(takeUntilDestroyed(this.destroy)).pipe(tap((list)=>{
            this.list.set(list);
        })).subscribe();
    }

}

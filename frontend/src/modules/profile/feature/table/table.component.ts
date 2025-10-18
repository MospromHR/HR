import {Component, DestroyRef, OnInit} from '@angular/core';
import {TuiTable} from '@taiga-ui/addon-table';
import {InternshipService} from "../../data-access/internship.service";
import {AsyncPipe} from "@angular/common";
import {of} from "rxjs";
import {InternshipCell} from "./interfaces";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";
import {ButtonComponent} from "../../ui/button/button.component";
import {RouterLink} from "@angular/router";


@Component({
    selector: 'profile-table',
    imports: [
        TuiTable,
        AsyncPipe,
        ButtonComponent,
        RouterLink
    ],
    providers: [InternshipService],
    templateUrl: './table.component.html',
    styleUrl: './table.component.less'
})
export class TableComponent implements OnInit {
    tableData$ = of([] as InternshipCell[]);
    protected readonly columns = ['period', 'type', 'course', 'capacity', 'description', 'status'];

    constructor(private internshipService: InternshipService,
                private destroyRef: DestroyRef) {
    }

    ngOnInit(): void {
        this.loadData();
    }

    publish(id: string): void {
        this.internshipService.publishEducationInternships(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(
            () => {
                //простите!
                this.loadData();
            }
        )
    }

    getCodes(id: string, count: number): void {
        this.internshipService.getCodes(id, count).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(
            () => {
                //простите!
                // this.loadData();
            }
        )
    }

    private loadData(): void {
        this.tableData$ = this.internshipService.getEducationInternships()
    }
}

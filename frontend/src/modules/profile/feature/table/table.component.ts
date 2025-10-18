import {Component, OnInit} from '@angular/core';
import {TuiTable} from '@taiga-ui/addon-table';
import {InternshipService} from "../../data-access/internship.service";
import {AsyncPipe} from "@angular/common";
import {of} from "rxjs";
import {InternshipCell} from "./interfaces";


@Component({
    selector: 'profile-table',
    imports: [
        TuiTable,
        AsyncPipe
    ],
    providers: [InternshipService],
    templateUrl: './table.component.html',
    styleUrl: './table.component.less'
})
export class TableComponent implements OnInit{
    tableData$ = of([] as InternshipCell[]);
    protected readonly columns = ['period', 'type', 'direction', 'well', 'company', 'status'];

    constructor(public internshipService: InternshipService) {
    }

    ngOnInit() {
        this.tableData$ = this.internshipService.getEducationInternships()
    }
}

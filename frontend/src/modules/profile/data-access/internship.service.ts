import {Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {map, Observable} from "rxjs";
import {http} from "../../../data-access/api.const";
import {ApiEducationInternship, ApiInternship} from "../../../data-access/api.interfaces";
import {InternshipCell} from "../feature/table/interfaces";

@Injectable()
export class InternshipService {
    constructor(private httpClient: HttpClient) {
    }

    getEducationInternships(): Observable<InternshipCell[]> {
        return this.httpClient.get<ApiEducationInternship[]>(`${http}/api/v1/me/education/internships`)
            .pipe(map((payload) =>
                payload.map((cell) => ({
                    id: cell.id,
                    period: cell.start_date + '-' + cell.end_date,
                    type: 'type',
                    direction: 'direction',
                    well: 'well',
                    company: 'company',
                    status: 'status'
                })))
            )
    }

    postEducationInternships(data: ApiInternship): Observable<boolean> {
        return this.httpClient.post<boolean>(`${http}/api/v1/me/education/internships`, data).pipe(map(() => true))
    }
}
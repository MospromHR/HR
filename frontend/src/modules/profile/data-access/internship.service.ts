import {Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {map, Observable, switchMap, tap} from "rxjs";
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
                    type: cell.type,
                    course: cell.course,
                    capacity: cell.capacity,
                    description: cell.description,
                    status: cell.status
                })))
            )
    }

    postEducationInternships(data: ApiInternship): Observable<boolean> {
        return this.httpClient.post<boolean>(`${http}/api/v1/me/education/internships`, data).pipe(map(() => true))
    }

    publishEducationInternships(id: string): Observable<boolean> {
        return this.httpClient.post<boolean>(`${http}/api/v1/me/education/internships/${id}/publish`,{})
    }

    getCodes(id: string, count: number): Observable<any>{
        return this.getCodesEducationInternshipsApi(id, count).pipe(
            switchMap(()=> this.getCodesEducationInternshipsDownloadApi(id))
        )
    }

   private getCodesEducationInternshipsApi(id: string, count: number): Observable<boolean> {
        return this.httpClient.post<boolean>(`${http}/api/v1/me/education/internships/${id}/codes`,{count})
    }

    private getCodesEducationInternshipsDownloadApi(id: string): Observable<any> {
        return this.httpClient.get<any>(`${http}/api/v1/me/education/internships/${id}/codes/download`,{
            responseType: 'blob' as 'json'
        }).pipe(
            tap((blob)=> {
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'Коды';
                link.click();
                window.URL.revokeObjectURL(url);
            })
        )
    }


}
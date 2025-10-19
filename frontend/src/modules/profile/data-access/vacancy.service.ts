import {Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {ApiPayloadVacancies, ApiVacancies} from "../../../data-access/api.interfaces";
import {map, Observable, tap} from "rxjs";
import {http} from "../../../data-access/api.const";
import {Vacancy} from "../feature/list/interfaces";

@Injectable()
export class VacancyService {
    constructor(private httpClient: HttpClient) {
    }

    postCompanyVacancies(data: ApiPayloadVacancies): Observable<boolean> {
        return this.httpClient.post<boolean>(`${http}/api/v1/me/company/vacancies`, data).pipe(map(() => true))
    }

    getShortVacancies(): Observable<Vacancy[]> {
        return this.getCompanyVacancies(4, 0).pipe(map((payload) =>
            payload.items.map(((item) => ({
            id: item.id,
            title: item.vacancyName,
            views: item.applicationsCount,
            responses: item.applicationsCount,
            conversion: item.applicationsCount/item.applicationsCount * 100,
        })))))
    }

    getCompanyVacancies(limit: number, offset: number): Observable<ApiVacancies> {
        return this.httpClient.get<ApiVacancies>(`${http}/api/v1/me/company/vacancies?limit=${limit}&offset=${offset}`
        )
    }
}
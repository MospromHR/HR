import {Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {map, Observable} from "rxjs";
import {http} from "../../../../data-access/api.const";

@Injectable({providedIn: 'root'})
export class AccountService {
    constructor(private httpClient: HttpClient) {
    }

    setCode(code: string): Observable<void> {
        return this.httpClient.post<boolean>(`${http}/api/v1/me/applicant/internships/activate`, {code}).pipe(map((response) => {

        }))
    }

}
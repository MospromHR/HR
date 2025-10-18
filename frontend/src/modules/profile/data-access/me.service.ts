import {Injectable} from "@angular/core";
import {Observable} from "rxjs";
import {ApiUser} from "../../../data-access/api.interfaces";
import {HttpClient} from "@angular/common/http";
import {http} from "../../../data-access/api.const";

@Injectable({
    providedIn: 'root',
})
export class MeService {
    constructor(private httpClient: HttpClient) {
    }

    getProfile(): Observable<ApiUser> {
        return this.httpClient.get<ApiUser>(`${http}/api/v1/me`);
    }
}
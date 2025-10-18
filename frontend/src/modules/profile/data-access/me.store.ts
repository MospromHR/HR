import {patchState, signalStore, withMethods, withState} from "@ngrx/signals";
import {ApiUser} from "../../../data-access/api.interfaces";
import {inject} from "@angular/core";
import {MeService} from "./me.service";
import {pipe, switchMap, tap} from "rxjs";
import {rxMethod} from "@ngrx/signals/rxjs-interop";


export interface MeState {
    me: ApiUser | null
}

const initialState: MeState = {
    me: null
}
export const MeStore = signalStore(
    {providedIn: 'root'},
    withState(initialState),
    withMethods(store => {
        const meService = inject(MeService);
        return {
            loadProfile: rxMethod<void>(
                pipe(
                    switchMap(() =>
                        meService.getProfile().pipe(
                            tap((me) => {
                                patchState(store, {me})
                            })
                        ))
                )
            )
        }
    })
)

export type MeStore = InstanceType<typeof MeStore>;
import {Component, effect} from '@angular/core';

import {ReactiveFormsModule} from '@angular/forms';

import {RouterOutlet} from '@angular/router';

@Component({
    selector: 'app-root',
    imports: [
        ReactiveFormsModule,
        RouterOutlet
    ],
    templateUrl: './app.html',
    styleUrl: './app.less'
})
export class App {

}

import {Component} from '@angular/core';
import {RouterOutlet} from '@angular/router';
import {NavComponent} from "../../ui/nav/nav.component";
import {TuiRoot} from "@taiga-ui/core";

@Component({
  selector: 'profile',
    imports: [
        RouterOutlet,
        NavComponent,
        TuiRoot
    ],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.less'
})
export class ProfileComponent {

}

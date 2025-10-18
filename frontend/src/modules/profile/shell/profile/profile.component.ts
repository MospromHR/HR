import {Component} from '@angular/core';
import {RouterOutlet} from '@angular/router';
import {NavComponent} from "../../ui/nav/nav.component";

@Component({
  selector: 'profile',
    imports: [
        RouterOutlet,
        NavComponent
    ],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.less'
})
export class ProfileComponent {

}

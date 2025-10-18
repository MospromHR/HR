import {Component, input} from '@angular/core';

@Component({
  selector: 'auth-role-item',
  imports: [],
  templateUrl: './role-item.component.html',
  styleUrl: './role-item.component.less'
})
export class RoleItemComponent {
  title = input.required<string>();
  subtitle = input.required<string>();
  isSelected = input(false);
}

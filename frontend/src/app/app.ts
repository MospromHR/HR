import {Component} from '@angular/core';

import {FormControl, FormGroup, ReactiveFormsModule} from '@angular/forms';

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
  protected readonly form = new FormGroup({
    user: new FormControl(''),
  });

  items = ['1', '2', '3'];
}

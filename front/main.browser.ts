import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { AppModule } from './app';

import 'zone.js';
platformBrowserDynamic()
  .bootstrapModule(AppModule)
  .catch(err => console.error(err));


import { defineConfig } from 'eslint/config';
import { rulesJs, rulesStylistic } from './eslint.common.js';

export default defineConfig([
  {
    languageOptions: {
      globals: { 'setTimeout': false, 'btoa': false }
    }
  },
  rulesJs,
  rulesStylistic
]);

import globals from 'globals';
import { defineConfig } from 'eslint/config';
import { rulesJs, rulesStylistic } from '../common/eslint.common.js';

export default defineConfig([
  {
    languageOptions: {
      globals: { ...globals.node }
    }
  },
  rulesJs,
  rulesStylistic
]);

import globals from 'globals';
import { defineConfig } from 'eslint/config';
import { rulesJs, rulesStylistic } from '../common/eslint.common.js';
import svelte from 'eslint-plugin-svelte';

export default defineConfig([
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.webextensions }
    }
  },
  rulesJs,
  { // js ignores
    files: ['**/*.svelte'],
    rules: {
      'init-declarations': 0,
      'no-use-before-define': 0,
      'prefer-const': 0,
      'no-unmodified-loop-condition': 0
    }
  },
  rulesStylistic,
  // no stylistic ignores
  ...svelte.configs['flat/recommended'],
  { // svelte ignores
    rules: {
      'svelte/require-each-key': 0,
      'svelte/no-navigation-without-resolve': 0,
      'svelte/no-useless-mustaches': 0
    }
  }
]);

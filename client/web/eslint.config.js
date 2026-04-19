import globals from 'globals';
import { defineConfig } from 'eslint/config';
import { rulesJs, rulesStylistic } from '../common/eslint.common.js';
import svelte from 'eslint-plugin-svelte';

export default defineConfig([
  {
    languageOptions: {
      globals: { ...globals.browser, 'google': false }
    }
  },
  rulesJs,
  { // js ignores
    files: ['**/*.svelte'],
    rules: {
      'no-nested-ternary': 1,
      'init-declarations': 0,
      'no-use-before-define': 0,
      'prefer-const': 0,
      'no-unmodified-loop-condition': 0,
      'no-invalid-this': 0,
      'max-lines': 0,
      'no-new': 0
    }
  },
  rulesStylistic,
  { // stylistic ignores
    files: ['**/*.svelte'],
    rules: {
      '@stylistic/quote-props': 0,
      '@stylistic/indent': 0,
      '@stylistic/object-curly-newline': 0,
      '@stylistic/indent-binary-ops': 0,
      '@stylistic/function-paren-newline': 0
    }
  },
  ...svelte.configs['flat/recommended'],
  { // svelte ignores
    rules: {
      'svelte/no-at-html-tags': 1,
      'svelte/require-each-key': 0,
      'svelte/no-navigation-without-resolve': 0,
      'svelte/no-useless-mustaches': 0,
      'svelte/no-reactive-reassign': 0
    }
  }
]);

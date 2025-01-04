import globals from 'globals';
import js from '@eslint/js';
import stylisticJs from '@stylistic/eslint-plugin-js';
import eslintPluginSvelte from 'eslint-plugin-svelte';

export default [
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        'google': false
      }
    }
  },
  ...eslintPluginSvelte.configs['flat/all'],
  {
    rules: {
      'svelte/no-unused-class-name': 0,
      'svelte/no-inline-styles': 0,
      'svelte/max-attributes-per-line': 0,
      'svelte/sort-attributes': 0,
      'svelte/require-each-key': 0,
      'svelte/html-self-closing': 0,
      'svelte/sort-attributes': 0,
      'svelte/button-has-type': 0,
      'svelte/first-attribute-linebreak': 0,
      'svelte/indent': 0,
      'svelte/html-closing-bracket-new-line': 0,
      'svelte/prefer-destructured-store-props': 0,
      'svelte/no-target-blank': 0,
      'svelte/no-useless-mustaches': 0,
      'svelte/require-stores-init': 0,
      // ^^^ above same as extension ^^^
      'svelte/no-reactive-reassign': 0,
      'svelte/shorthand-directive': 0,
      'svelte/shorthand-attribute': 0,
      'svelte/prefer-style-directive' : 0,
      'svelte/no-goto-without-base': 0
    }
  },
  js.configs.recommended,
  {
    rules: {
      'no-self-assign': 0
    }
  },
  {
    plugins: {
      '@stylistic/js': stylisticJs
    },
    rules: {
      '@stylistic/js/semi': [2, 'always'],
      'svelte/no-at-html-tags': 1
    }
  }
];

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
      'svelte/no-goto-without-base': 0,
      'svelte/no-at-html-tags': 0
    }
  },
  js.configs.all,
  {
    rules: {
      'no-plusplus': [2, { 'allowForLoopAfterthoughts': true }],
      'no-self-assign': 0,
      'prefer-const': 0,
      'no-new': 0,
      'one-var': 0,
      'func-style': 0,
      'func-names': 0,
      'id-length': 0,
      'no-eq-null': 0,
      'eqeqeq': 0,
      'curly': 0,
      'no-magic-numbers': 0,
      'no-inline-comments': 0,
      'no-param-reassign': 0,
      'sort-keys': 0,
      'max-lines': 0,
      'max-statements': 0,
      'prefer-template': 0,
      'prefer-arrow-callback': 0,
      'no-ternary': 0,
      'no-await-in-loop': 0,
      'no-invalid-this': 0,
      'object-shorthand': 0,
      'no-useless-assignment': 0,
      'init-declarations': 0,
      'no-use-before-define': 0,
      'max-lines-per-function': 0,
      'prefer-destructuring': 0,
      'require-unicode-regexp': 0,
      'max-classes-per-file': 0,
      'no-unmodified-loop-condition': 0,
      'consistent-return': 0,
      'sort-imports': 0
    }
  },
  {
    plugins: {
      '@stylistic/js': stylisticJs
    },
    rules: {
      '@stylistic/js/semi': [2, 'always']
    }
  }
];

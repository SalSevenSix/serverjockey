import globals from 'globals';
import js from '@eslint/js';
import stylisticJs from '@stylistic/eslint-plugin-js';

export default [
  {
    languageOptions: {
      globals: {
        ...globals.node
      }
    }
  },
  js.configs.all,
  {
    rules: {
      'no-use-before-define': 0,  // TODO fix this
      'prefer-destructuring': 0,  // TODO investigate more
      'no-plusplus': [2, { 'allowForLoopAfterthoughts': true }],
      'curly': 0,
      'sort-keys': 0,
      'id-length': 0,
      'eqeqeq': 0,
      'no-eq-null': 0,
      'one-var': 0,
      'prefer-template': 0,
      'prefer-named-capture-group': 0,
      'require-unicode-regexp': 0,
      'max-statements': 0,
      'max-params': 0,
      'func-style': 0,
      'func-names': 0,
      'no-param-reassign': 0,
      'no-magic-numbers': 0,
      'no-ternary': 0,
      'no-console': 0,
      'no-useless-assignment': 0,
      'prefer-arrow-callback': 0,
      'guard-for-in': 0,
      'consistent-return': 0,
      'no-await-in-loop': 0,
      'no-inline-comments': 0,
      'object-shorthand': 0,
      'no-template-curly-in-string': 0,
      'consistent-this': 0
    }
  },
  {
    plugins: {
      '@stylistic/js': stylisticJs
    },
    rules: {
      '@stylistic/js/semi': ['error', 'always']
    }
  }
];

import globals from 'globals';
import { defineConfig } from "eslint/config";
import js from "@eslint/js";
import stylistic from '@stylistic/eslint-plugin';

export default defineConfig([
  {
    languageOptions: { globals: { ...globals.node } }
  },
  {
    plugins: { js }, extends: ['js/all'], rules: {
      'no-plusplus': [2, { 'allowForLoopAfterthoughts': true }],
      'no-warning-comments': 1,
      'require-atomic-updates': 1,
      'require-await': 1,
      'prefer-destructuring': 0,
      'curly': 0,
      'sort-keys': 0,
      'id-length': 0,
      'eqeqeq': 0,
      'no-eq-null': 0,
      'one-var': 0,
      'prefer-template': 0,
      'max-statements': 0,
      'max-params': 0,
      'func-style': 0,
      'func-names': 0,
      'no-param-reassign': 0,
      'no-magic-numbers': 0,
      'no-ternary': 0,
      'no-useless-assignment': 0,
      'prefer-arrow-callback': 0,
      'no-inline-comments': 0,
      'object-shorthand': 0,
      'sort-imports': 0,
      'prefer-named-capture-group': 0,
      'require-unicode-regexp': 0,
      'consistent-return': 0,
      'no-await-in-loop': 0,
      'no-template-curly-in-string': 0
    }
  },
  {
    plugins: { '@stylistic': stylistic }, extends: ['@stylistic/all'], rules: {
      '@stylistic/indent': [2, 2],
      '@stylistic/no-multi-spaces': [2, { ignoreEOLComments: true }],
      '@stylistic/object-curly-spacing': [2, 'always'],
      '@stylistic/padded-blocks': [2, 'never'],
      '@stylistic/quote-props': [2, 'consistent-as-needed'],
      '@stylistic/quotes': [2, 'single'],
      '@stylistic/semi': [2, 'always'],
      '@stylistic/space-before-function-paren': [2, 'never'],
      '@stylistic/function-paren-newline': 2,
      '@stylistic/no-extra-parens': 1,
      '@stylistic/array-element-newline': 0,
      '@stylistic/multiline-ternary': 0,
      '@stylistic/object-property-newline': 0,
      '@stylistic/brace-style': 0,
      '@stylistic/function-call-argument-newline': 0,
      '@stylistic/newline-per-chained-call': 0,
      '@stylistic/dot-location': 0,
      '@stylistic/array-bracket-newline': 0
    }
  }
]);

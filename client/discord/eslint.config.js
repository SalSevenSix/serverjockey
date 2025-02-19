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
      'require-atomic-updates': 1,
      'no-plusplus': [2, { 'allowForLoopAfterthoughts': true }],
      'prefer-destructuring': 0,
      'no-warning-comments': 0,
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
      '@stylistic/js/array-bracket-spacing': 2,
      '@stylistic/js/block-spacing': 2,
      '@stylistic/js/comma-dangle': 2,
      '@stylistic/js/comma-spacing': 2,
      '@stylistic/js/comma-style': 2,
      '@stylistic/js/computed-property-spacing': 2,
      '@stylistic/js/eol-last': 2,
      '@stylistic/js/func-call-spacing': 2,
      '@stylistic/js/function-call-spacing': 2,
      '@stylistic/js/function-paren-newline': 2,
      '@stylistic/js/generator-star-spacing': 2,
      '@stylistic/js/indent': [2, 2],
      '@stylistic/js/key-spacing': 2,
      '@stylistic/js/keyword-spacing': 2,
      '@stylistic/js/linebreak-style': 2,
      '@stylistic/js/lines-between-class-members': 2,
      '@stylistic/js/max-len': [2, { code: 120 }],
      '@stylistic/js/max-statements-per-line': [2, { max: 2 }],
      '@stylistic/js/multiline-comment-style': 2,
      '@stylistic/js/new-parens': 2,
      '@stylistic/js/no-confusing-arrow': 2,
      '@stylistic/js/no-extra-parens': 2,
      '@stylistic/js/no-extra-semi': 2,
      '@stylistic/js/no-floating-decimal': 2,
      '@stylistic/js/no-mixed-operators': 2,
      '@stylistic/js/no-mixed-spaces-and-tabs': 2,
      '@stylistic/js/no-multi-spaces': [2, { ignoreEOLComments: true }],
      '@stylistic/js/no-multiple-empty-lines': 2,
      '@stylistic/js/no-tabs': 2,
      '@stylistic/js/no-trailing-spaces': 2,
      '@stylistic/js/no-whitespace-before-property': 2,
      '@stylistic/js/nonblock-statement-body-position': 2,
      '@stylistic/js/object-curly-newline': 2,
      '@stylistic/js/object-curly-spacing': [2, 'always'],
      '@stylistic/js/one-var-declaration-per-line': 2,
      '@stylistic/js/operator-linebreak': 2,
      '@stylistic/js/padded-blocks': [2, 'never'],
      '@stylistic/js/padding-line-between-statements': 2,
      '@stylistic/js/quote-props': [2, 'consistent-as-needed'],
      '@stylistic/js/quotes': [2, 'single'],
      '@stylistic/js/rest-spread-spacing': 2,
      '@stylistic/js/semi': [2, 'always'],
      '@stylistic/js/semi-spacing': 2,
      '@stylistic/js/semi-style': 2,
      '@stylistic/js/space-before-blocks': 2,
      '@stylistic/js/space-before-function-paren': [2, 'never'],
      '@stylistic/js/space-in-parens': 2,
      '@stylistic/js/space-infix-ops': 2,
      '@stylistic/js/space-unary-ops': 2,
      '@stylistic/js/spaced-comment': 2,
      '@stylistic/js/switch-colon-spacing': 2,
      '@stylistic/js/template-curly-spacing': 2,
      '@stylistic/js/template-tag-spacing': 2,
      '@stylistic/js/wrap-iife': 2,
      '@stylistic/js/wrap-regex': 2,
      '@stylistic/js/yield-star-spacing': 2
    }
  }
];

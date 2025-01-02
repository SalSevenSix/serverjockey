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
  js.configs.recommended,
  {
    plugins: {
      '@stylistic/js': stylisticJs
    },
    rules: {
      '@stylistic/js/semi': ['error', 'always']
    }
  }
];

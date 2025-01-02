import eslintPluginSvelte from 'eslint-plugin-svelte';
import stylisticJs from '@stylistic/eslint-plugin-js';

export default [
  ...eslintPluginSvelte.configs['flat/recommended'],
  {
    plugins: {
      '@stylistic/js': stylisticJs
    },
    rules: {
      '@stylistic/js/semi': ['error', 'always']
    }
  }
];

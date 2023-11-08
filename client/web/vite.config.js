import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
    proxy: {
      '/login': 'http://localhost:6164',
      '/modules': 'http://localhost:6164',
      '/system': 'http://localhost:6164',
      '/instances': 'http://localhost:6164',
      '/store': 'http://localhost:6164',
      '/subscriptions': 'http://localhost:6164'
    }
  }
});

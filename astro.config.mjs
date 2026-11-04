import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// The address is a placeholder until the domain is registered; change `site` then (canonical links and the sitemap use it).
export default defineConfig({
  site: 'https://techversation.example',
  trailingSlash: 'always',
  compressHTML: false,
  build: { format: 'directory' },
  integrations: [sitemap()],
});

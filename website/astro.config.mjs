import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import fs from 'node:fs';

// Auto-detect custom domain:
// 1. Environment variable CUSTOM_DOMAIN === 'true' or SITE_URL === 'https://notthistime.site'
// 2. Or presence of public/CNAME or CNAME file in root
const hasCNAME = fs.existsSync('./public/CNAME') || fs.existsSync('./CNAME');
const isCustomDomain = process.env.CUSTOM_DOMAIN === 'true' ||
                       process.env.SITE_URL === 'https://notthistime.site' ||
                       hasCNAME;

const site = isCustomDomain 
  ? 'https://notthistime.site' 
  : 'https://feeline03.github.io';

const base = isCustomDomain ? '/' : '/notthistime';

export default defineConfig({
  site,
  base,
  integrations: [
    tailwind(),
    sitemap({
      filter: (page) => !page.includes('/404')
    })
  ]
});

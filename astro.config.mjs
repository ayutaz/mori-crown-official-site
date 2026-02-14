import { defineConfig } from 'astro/config';

const repo = process.env.GITHUB_REPOSITORY?.split('/')[1] ?? '';
const isUserSite = repo.endsWith('.github.io');
const base = repo && !isUserSite ? `/${repo}` : '/';

export default defineConfig({
  site: 'https://s19447.github.io',
  base,
  trailingSlash: 'always'
});

/**
 * Helper to prepend Astro's BASE_URL to internal routes and assets.
 * Seamlessly adapts between GitHub Pages subpath (/notthistime/) and custom domain (/).
 */
export function withBase(path: string = '/'): string {
  // BASE_URL is typically '/notthistime/' or '/'
  const rawBase = import.meta.env.BASE_URL || '/';
  const cleanBase = rawBase.replace(/\/+$/, '');

  if (!path || path === '/') {
    return cleanBase ? `${cleanBase}/` : '/';
  }

  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${cleanBase}${cleanPath}`;
}

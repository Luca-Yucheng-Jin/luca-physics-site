/** Cloudflare Worker entry for the static Vite build. */
const worker = {
  async fetch(request, env) {
    const direct = await env.ASSETS.fetch(request);
    if (direct.status !== 404) return direct;

    const url = new URL(request.url);
    const lastSegment = url.pathname.split('/').pop() || '';

    if (url.pathname.endsWith('/')) {
      url.pathname += 'index.html';
    } else if (!lastSegment.includes('.')) {
      url.pathname += '.html';
    } else {
      return direct;
    }

    return env.ASSETS.fetch(new Request(url, request));
  },
};

export default worker;

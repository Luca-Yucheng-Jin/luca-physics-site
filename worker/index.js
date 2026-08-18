/** Cloudflare Worker entry for the static Vite build. */
const worker = {
  async fetch(request, env) {
    const requestUrl = new URL(request.url);
    if (requestUrl.pathname === '/reading' || requestUrl.pathname === '/reading.html') {
      return Response.redirect(new URL('/notes.html', requestUrl), 308);
    }

    const direct = await env.ASSETS.fetch(request);
    if (direct.status !== 404) return direct;

    const url = requestUrl;
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

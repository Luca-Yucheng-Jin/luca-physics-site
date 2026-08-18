/** Cloudflare Worker entry for the static Vite build. */
function addPdfCanonical(response, requestUrl) {
  if (response.status === 404) return response;
  const match = requestUrl.pathname.match(/^\/output\/pdf\/([a-z0-9-]+)\.pdf$/i);
  if (!match) return response;

  const canonical = new URL(`/notes/${match[1]}.html`, requestUrl);
  const headers = new Headers(response.headers);
  headers.set('Link', `<${canonical.href}>; rel="canonical"`);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

const worker = {
  async fetch(request, env) {
    const requestUrl = new URL(request.url);
    if (requestUrl.pathname === '/reading' || requestUrl.pathname === '/reading.html') {
      return Response.redirect(new URL('/notes.html', requestUrl), 308);
    }

    const isRetiredResearchRoute =
      requestUrl.pathname === '/research' ||
      requestUrl.pathname === '/research.html' ||
      requestUrl.pathname === '/research/' ||
      requestUrl.pathname.startsWith('/research/') ||
      /^\/output\/pdf\/research-[^/]+\.pdf$/.test(requestUrl.pathname);
    if (isRetiredResearchRoute) {
      return Response.redirect(new URL('/', requestUrl), 308);
    }

    if (requestUrl.pathname === '/index.html') {
      return Response.redirect(new URL('/', requestUrl), 308);
    }

    const direct = await env.ASSETS.fetch(request);
    if (direct.status !== 404) return addPdfCanonical(direct, requestUrl);

    const url = new URL(requestUrl);
    const lastSegment = url.pathname.split('/').pop() || '';

    if (url.pathname.endsWith('/')) {
      url.pathname += 'index.html';
    } else if (!lastSegment.includes('.')) {
      url.pathname += '.html';
      const html = await env.ASSETS.fetch(new Request(url, request));
      if (html.status === 404) return direct;
      return Response.redirect(url, 308);
    } else {
      return direct;
    }

    return addPdfCanonical(await env.ASSETS.fetch(new Request(url, request)), requestUrl);
  },
};

export default worker;

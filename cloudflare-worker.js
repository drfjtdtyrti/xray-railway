/**
 * Ultra Gaming VPN — Cloudflare Worker
 * Proxies WebSocket + HTTPUpgrade + SplitHTTP to Railway
 *
 * Paths routed:
 *   /vless    → VLESS WS
 *   /vmess    → VMess WS
 *   /trojan   → Trojan WS
 *   /upgrade  → VLESS HTTPUpgrade  ← best for gaming
 *   /split    → VLESS SplitHTTP
 */

const UPSTREAM = "xray-core-production-f4b1.up.railway.app";

const ALLOWED_PATHS = ["/vless", "/vmess", "/trojan", "/upgrade", "/split"];

export default {
  async fetch(request, env, ctx) {
    const url  = new URL(request.url);
    const path = url.pathname;

    // ── Keepalive ping ──────────────────────────────────────────────────────
    if (path === "/ping") {
      return new Response("pong", { status: 200 });
    }

    // ── Route proxy paths ───────────────────────────────────────────────────
    const matched = ALLOWED_PATHS.find(p => path.startsWith(p));
    if (!matched) {
      return new Response("Not found", { status: 404 });
    }

    const upgrade = request.headers.get("Upgrade");

    if (upgrade && upgrade.toLowerCase() === "websocket") {
      return handleWebSocket(request, url, ctx);
    } else {
      return handleHTTP(request, url);
    }
  },

  async scheduled(event, env, ctx) {
    // Cron keepalive — runs every minute (set in Worker dashboard)
    ctx.waitUntil(
      fetch(`https://${UPSTREAM}/health`).catch(() => {})
    );
  },
};

// ── WebSocket Proxy ──────────────────────────────────────────────────────────

async function handleWebSocket(request, url, ctx) {
  const targetUrl = `wss://${UPSTREAM}${url.pathname}${url.search}`;

  const upstreamReq = new Request(targetUrl, {
    headers: buildHeaders(request, UPSTREAM),
  });

  const [client, upstreamWs] = Object.values(new WebSocketPair());
  const upstream = await fetch(upstreamReq, {
    headers: upstreamReq.headers,
  });

  if (upstream.webSocket) {
    const ws = upstream.webSocket;
    ws.accept();
    client.accept();

    // pipe: client → upstream
    client.addEventListener("message", ({ data }) => {
      try { ws.send(data); } catch (_) {}
    });
    client.addEventListener("close", ({ code, reason }) => {
      try { ws.close(code, reason); } catch (_) {}
    });
    client.addEventListener("error", () => {
      try { ws.close(1011, "client error"); } catch (_) {}
    });

    // pipe: upstream → client
    ws.addEventListener("message", ({ data }) => {
      try { client.send(data); } catch (_) {}
    });
    ws.addEventListener("close", ({ code, reason }) => {
      try { client.close(code, reason); } catch (_) {}
    });
    ws.addEventListener("error", () => {
      try { client.close(1011, "upstream error"); } catch (_) {}
    });

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }

  return new Response("WebSocket upgrade failed", { status: 502 });
}

// ── HTTP Proxy (HTTPUpgrade / SplitHTTP) ────────────────────────────────────

async function handleHTTP(request, url) {
  const targetUrl = `https://${UPSTREAM}${url.pathname}${url.search}`;

  const headers = buildHeaders(request, UPSTREAM);

  const proxyReq = new Request(targetUrl, {
    method:  request.method,
    headers: headers,
    body:    request.body,
    redirect: "follow",
  });

  const resp = await fetch(proxyReq);

  const respHeaders = new Headers(resp.headers);
  respHeaders.set("Access-Control-Allow-Origin", "*");

  return new Response(resp.body, {
    status:  resp.status,
    headers: respHeaders,
  });
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function buildHeaders(request, host) {
  const h = new Headers(request.headers);
  h.set("Host", host);
  // Strip CF-specific headers that might confuse upstream
  h.delete("CF-Connecting-IP");
  h.delete("CF-IPCountry");
  h.delete("CF-RAY");
  h.delete("CF-Visitor");
  return h;
}

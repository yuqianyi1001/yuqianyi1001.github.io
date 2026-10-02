// Telegram relay for scripts/wechat_auto_sync.py.
//
// The Beijing server cannot reach api.telegram.org (nor *.workers.dev), so it posts
// to this Worker on a custom domain instead:
//
//   POST /   Authorization: Bearer <RELAY_SECRET>   {"text": "..."}
//
// The Worker sends the text to one fixed chat. The bot token and the chat id are
// Worker secrets; a caller can neither choose the recipient nor see the token.
//
// Secrets (wrangler secret put): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, RELAY_SECRET.

const same = (a, b) => {
  // constant-time comparison
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
};

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') return new Response('not found', { status: 404 });
    const auth = request.headers.get('Authorization') || '';
    if (!env.RELAY_SECRET || !same(auth, `Bearer ${env.RELAY_SECRET}`)) {
      return new Response('unauthorized', { status: 401 });
    }
    let text;
    try {
      text = String((await request.json()).text || '').slice(0, 4000);
    } catch {
      return new Response('bad request', { status: 400 });
    }
    if (!text) return new Response('bad request', { status: 400 });

    const reply = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text, disable_web_page_preview: true }),
    });
    // Telegram's own answer can echo request details; pass on only the outcome.
    return new Response(reply.ok ? 'sent' : `telegram error ${reply.status}`, { status: reply.ok ? 200 : 502 });
  },
};

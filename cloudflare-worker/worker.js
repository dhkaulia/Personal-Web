/**
 * Cloudflare Worker for Mabar Waiting List
 * Serverless, 24/7 online, free tier compatible.
 *
 * Can receive:
 * 1. Webhook POST /api/queue from Discord interactions or HTTP requests
 * 2. Webhook GET /api/queue for your personal website to fetch live
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Set CORS headers
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Secret-Token",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders, status: 204 });
    }

    // Default queue fallback
    const DEFAULT_QUEUE = [
      { id: "1", name: "Keyaru", games: 6, tier: "VIP", status: "playing", joinedAt: "11:30 WIB" },
      { id: "2", name: "Freydhite", games: 3, tier: "SVIP", status: "waiting", joinedAt: "12:15 WIB" }
    ];

    // GET /api/queue
    if (request.method === "GET" && (url.pathname === "/api/queue" || url.pathname === "/")) {
      let queue = DEFAULT_QUEUE;
      if (env.QUEUE_KV) {
        const stored = await env.QUEUE_KV.get("mabar_queue", "json");
        if (stored) queue = stored;
      }
      return new Response(JSON.stringify(queue), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // POST /api/queue or /api/webhook
    if (request.method === "POST" && (url.pathname === "/api/queue" || url.pathname === "/api/webhook")) {
      try {
        const body = await request.json();
        let queue = DEFAULT_QUEUE;
        if (env.QUEUE_KV) {
          const stored = await env.QUEUE_KV.get("mabar_queue", "json");
          if (stored) queue = stored;
        }

        const action = (body.action || "add").toLowerCase();
        const name = body.name;
        const games = body.games;
        const tier = (body.tier || "VIP").toUpperCase();

        if (action === "add") {
          const existing = queue.find(p => p.name.toLowerCase() === name.toLowerCase());
          if (existing) {
            existing.games = Number(games);
            if (body.tier) existing.tier = tier;
          } else {
            queue.push({
              id: String(queue.length + 1),
              name,
              games: Number(games || 1),
              tier,
              status: queue.length === 0 ? "playing" : (queue.length === 1 ? "next" : "waiting"),
              joinedAt: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) + " WIB"
            });
          }
        } else if (action === "set" || action === "update") {
          const existing = queue.find(p => p.name.toLowerCase() === name.toLowerCase());
          if (!existing) {
            return new Response(JSON.stringify({ error: `Player ${name} not found` }), { status: 404, headers: corsHeaders });
          }
          existing.games = Number(games);
          if (body.tier) existing.tier = tier;
        } else if (action === "decrement" || action === "dec") {
          const existing = queue.find(p => p.name.toLowerCase() === name.toLowerCase());
          if (!existing) {
            return new Response(JSON.stringify({ error: `Player ${name} not found` }), { status: 404, headers: corsHeaders });
          }
          existing.games = Math.max(0, Number(existing.games || 1) - 1);
        } else if (action === "remove") {
          queue = queue.filter(p => p.name.toLowerCase() !== name.toLowerCase());
          if (queue.length > 0) queue[0].status = "playing";
          if (queue.length > 1) queue[1].status = "next";
        } else if (action === "clear") {
          queue = [];
        }

        if (env.QUEUE_KV) {
          await env.QUEUE_KV.put("mabar_queue", JSON.stringify(queue));
        }

        return new Response(JSON.stringify({ success: true, queue }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), { status: 400, headers: corsHeaders });
      }
    }

    return new Response(JSON.stringify({ error: "Endpoint not found" }), { status: 404, headers: corsHeaders });
  }
};

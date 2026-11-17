/* Entry of the site on Cloudflare Workers.
   A request for the relay is passed to functions/api/record.js; every other request is
   answered with the files of the build. */

import { onRequestGet } from "./functions/api/record.js";

const RELAY_PATH = "/api/record";

export default {
  async fetch(request, env) {
    if (new URL(request.url).pathname !== RELAY_PATH) {
      return env.ASSETS.fetch(request);
    }
    if (request.method !== "GET") {
      return new Response(null, { status: 405, headers: { Allow: "GET" } });
    }
    return onRequestGet({ request, env });
  },
};

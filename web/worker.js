/* Entry of the site on Cloudflare Workers.
   A request for one of the two relays is passed to its file under functions/api, when it comes
   with the method of that relay; every other request is answered with the files of the build. */

import { onRequestPost } from "./functions/api/reading.js";
import { onRequestGet } from "./functions/api/record.js";

const RELAYS = new Map([
  ["/api/record", { method: "GET", answer: onRequestGet }],      // catalogue of the portal
  ["/api/reading", { method: "POST", answer: onRequestPost }],   // model of the second reading
]);

export default {
  async fetch(request, env) {
    const relay = RELAYS.get(new URL(request.url).pathname);
    if (!relay) {
      return env.ASSETS.fetch(request);
    }
    if (request.method !== relay.method) {
      return new Response(null, { status: 405, headers: { Allow: relay.method } });
    }
    return relay.answer({ request, env });
  },
};

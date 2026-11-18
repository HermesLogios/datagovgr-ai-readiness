/* Relay of the public page to Jev, the model of TypeSafe AI that gives the second reading of a description.
   The address of the model does not accept calls from a web page, so the page sends here, in the body
   of a POST request, the key of the visitor and the request for the model. The relay passes on only
   the fields that the page sends, with the key in the Authorization header, and returns the reply of
   the model. The key and the texts are not kept and are written nowhere. */

const MODEL_ADDRESS = "https://api.typesafe.ai/v1/systemone";
const USER_AGENT = "datagovgr-ai-readiness/0.1 (research project; GFOSS internship)";
const TIMEOUT = 30000;                 // milliseconds to wait for the model
const MAX_BODY = 60000;                // characters of the body of a request
const MAX_BODY_BYTES = 4 * MAX_BODY;   // a character takes at most four bytes
const MAX_TEXT = 8000;                 // characters of one text of the state
const MAX_STATEMENT = 2000;            // characters of the instructions or of one criterion of a question
const MAX_RESOURCE_DESCRIPTIONS = 20;
const MAX_QUESTIONS = 10;
const KEY = /^[\x21-\x7e]{8,300}$/;
const MODEL = /^jev-[a-z0-9.]{1,20}$/;
const QUESTION_NAME = /^[a-z][a-z_]{0,29}$/;
const HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};

function answer(code, status) {
  return new Response(JSON.stringify({ error: code }), { status, headers: HEADERS });
}

function isTable(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isText(value, limit) {
  return typeof value === "string" && value.length <= limit;
}

function isStatement(value) {
  return isText(value, MAX_STATEMENT) && value.length > 0;
}

/* The texts of a dataset as the page sends them, or null. */
function cleanState(state) {
  if (!isTable(state)) {
    return null;
  }
  const { title, description, resource_descriptions: resources } = state;
  if (!isText(title, MAX_TEXT) || !isText(description, MAX_TEXT) || !Array.isArray(resources)
      || resources.length > MAX_RESOURCE_DESCRIPTIONS || !resources.every((text) => isText(text, MAX_TEXT))) {
    return null;
  }
  return { title, description, resource_descriptions: resources };
}

/* The questions of a request, each a statement whose probability is asked for, or null. */
function cleanQuestions(questions) {
  if (!isTable(questions)) {
    return null;
  }
  const names = Object.keys(questions);
  if (names.length < 1 || names.length > MAX_QUESTIONS) {
    return null;
  }
  const clean = {};
  for (const name of names) {
    const question = questions[name];
    if (!QUESTION_NAME.test(name) || !isTable(question) || question.type !== "noul" || !isStatement(question.instructions)) {
      return null;
    }
    clean[name] = { type: "noul", instructions: question.instructions };
    if (question.criteria !== undefined) {
      const criteria = question.criteria;
      if (!isTable(criteria) || !isStatement(criteria.true) || !isStatement(criteria.false)) {
        return null;
      }
      clean[name].criteria = { true: criteria.true, false: criteria.false };
    }
  }
  return clean;
}

/* The request for the model with the fields that the page sends and no other, or null. */
function cleanRequest(request) {
  if (!isTable(request) || typeof request.model !== "string" || !MODEL.test(request.model)) {
    return null;
  }
  const state = cleanState(request.state);
  const questions = cleanQuestions(request.questions);
  return state && questions ? { model: request.model, state, questions } : null;
}

/* Body of a request as text, or null when it is longer than a request of the page can be. */
async function bodyText(request) {
  if (!request.body || Number(request.headers.get("Content-Length") || 0) > MAX_BODY_BYTES) {
    return null;
  }
  const reader = request.body.getReader();
  const decoder = new TextDecoder();
  let text = "";
  let bytes = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    bytes += value.byteLength;
    if (bytes > MAX_BODY_BYTES) {
      await reader.cancel();
      return null;
    }
    text += decoder.decode(value, { stream: true });
  }
  text += decoder.decode();
  return text.length > MAX_BODY ? null : text;
}

/* Key and request of a POST request of the page, or null for anything else. */
async function sentByThePage(request) {
  const type = (request.headers.get("Content-Type") || "").split(";")[0].trim().toLowerCase();
  if (type !== "application/json") {
    return null;
  }
  const text = await bodyText(request);
  if (text === null) {
    return null;
  }
  let sent;
  try {
    sent = JSON.parse(text);
  } catch (error) {
    return null;
  }
  if (!isTable(sent) || typeof sent.key !== "string" || !KEY.test(sent.key)) {
    return null;
  }
  const clean = cleanRequest(sent.request);
  return clean ? { key: sent.key, request: clean } : null;
}

export async function onRequestPost({ request, env }) {
  const sent = await sentByThePage(request);
  if (sent === null) {
    return answer("request", 400);
  }
  const address = (env && env.TYPESAFE_API_URL) || MODEL_ADDRESS;
  try {
    const reply = await fetch(address, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${sent.key}`,
        "Content-Type": "application/json",
        Accept: "application/json",
        "User-Agent": USER_AGENT,
      },
      body: JSON.stringify(sent.request),
      signal: AbortSignal.timeout(TIMEOUT),
    });
    if (reply.status === 401 || reply.status === 403) {
      return answer("key", 401);
    }
    if (reply.status === 429) {
      return answer("limit", 429);
    }
    if (!reply.ok) {
      throw new Error(`HTTP ${reply.status}`);
    }
    const text = await reply.text();
    JSON.parse(text);
    return new Response(text, { status: 200, headers: HEADERS });
  } catch (error) {
    return answer("service", 502);
  }
}

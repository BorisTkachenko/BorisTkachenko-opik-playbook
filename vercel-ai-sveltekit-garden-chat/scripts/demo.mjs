// One command, start to finish: make sure the online-eval rule exists, build and boot the SvelteKit
// server, stream scripted multi-turn chats over HTTP, stop the server (which flushes traces to
// Opik), then poll Opik until the judge's scores show up on every trace.
import { spawn, spawnSync } from "node:child_process";
import { setTimeout as sleep } from "node:timers/promises";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadEnvFiles } from "./env.mjs";
import { opikClient, ensureRule, RULE_NAME, PROJECT_NAME } from "./rule.mjs";
import { waitForScores, report, summarize } from "./verify.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
loadEnvFiles(root);

const PORT = process.env.DEMO_PORT || "5471";
const BASE = `http://127.0.0.1:${PORT}`;

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// Two chats = two Opik threads. The last turn of chat B asks something the guide cannot answer.
const conversations = [
  {
    title: "Tomatoes on clay",
    turns: [
      "When can I plant tomatoes outside in Hollowbrook?",
      "My soil is heavy clay. How should I prepare the bed?",
      "Slugs keep eating my seedlings. What works?",
    ],
  },
  {
    title: "Blight, then an unanswerable question",
    turns: [
      "There are brown patches on my tomato leaves in late July. What is it and what do I do?",
      "Which brand of greenhouse heater is cheapest at the Hollowbrook garden centre this week?",
    ],
  },
];
const expectedTraces = conversations.reduce((n, c) => n + c.turns.length, 0);

const call = opikClient();

// 1. The rule must exist and be enabled BEFORE any trace arrives: Opik only scores traces that
//    are logged after a rule is active. ensureRule() looks it up by name first, so re-runs are safe.
const rule = await ensureRule(call);
console.log(`Online rule "${RULE_NAME}": ${rule.created ? "created" : "already present"} (${rule.id})`);

// 2. Build and boot the production server.
console.log("Building SvelteKit app...");
const build = spawnSync("npm", ["run", "build"], { cwd: root, stdio: "ignore" });
if (build.status !== 0) {
  console.error("Build failed; run `npm run build` to see why.");
  process.exit(1);
}
const startedAt = new Date().toISOString();
const server = spawn("node", ["build"], {
  cwd: root,
  env: { ...process.env, PORT, HOST: "127.0.0.1" },
  stdio: ["ignore", "pipe", "pipe"],
});
server.stdout.on("data", () => {});
server.stderr.on("data", (d) => process.stderr.write(d));
const exited = new Promise((resolve) => server.once("exit", resolve));

async function waitForServer(timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(BASE, { signal: AbortSignal.timeout(2000) })).ok) return;
    } catch {
      /* not up yet */
    }
    await sleep(300);
  }
  throw new Error("Server did not become ready in time");
}

// Same request the browser's Chat class sends: the chat id plus the whole history, answered as an SSE stream.
async function chatTurn(chatId, messages) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: chatId, messages }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  let text = "";
  let buffer = "";
  const decoder = new TextDecoder();
  for await (const chunk of res.body) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
      try {
        const event = JSON.parse(line.slice(6));
        if (event.type === "text-delta" && event.delta) {
          text += event.delta;
          process.stdout.write(event.delta);
        }
      } catch {
        /* ignore keepalives */
      }
    }
  }
  process.stdout.write("\n");
  return text;
}

const message = (role, text) => ({ id: randomUUID(), role, parts: [{ type: "text", text }] });

let failed = false;
try {
  await waitForServer();
  console.log(`Server ready on ${BASE}\n`);
  for (const conversation of conversations) {
    const chatId = randomUUID();
    console.log(`=== ${conversation.title} (thread ${chatId.slice(0, 8)}) ===`);
    const history = [];
    for (const turn of conversation.turns) {
      console.log(`\nYou: ${turn}\nSprout: `);
      history.push(message("user", turn));
      history.push(message("assistant", await chatTurn(chatId, history)));
    }
    console.log();
  }
} catch (err) {
  failed = true;
  console.error(err);
} finally {
  // 3. SIGTERM makes the server flush its batched spans to Opik (see src/hooks.server.ts), then exit.
  server.kill("SIGTERM");
  await Promise.race([exited, sleep(15_000)]);
  if (server.exitCode === null) server.kill("SIGKILL");
}
if (failed) process.exit(1);

// 4. The judge runs inside Opik, asynchronously, so poll until every trace has both scores.
console.log("Waiting for the online rule to score the traces...");
const traces = await waitForScores(call, startedAt, expectedTraces);
console.table(await report(call, traces));
const { total, scored } = summarize(traces);
console.log(`Project ${PROJECT_NAME}: ${total} traces, ${scored} fully scored by ${RULE_NAME}.`);
if (total < expectedTraces || scored < expectedTraces) {
  console.error("Not every trace was scored in time.");
  process.exit(1);
}

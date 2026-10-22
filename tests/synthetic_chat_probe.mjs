// Local-only structural event recorder. No real website or account is accessed.
import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { resolve, dirname } from "node:path";
import { chromium } from "playwright";

const fixture = resolve(dirname(fileURLToPath(import.meta.url)), "fixtures", "synthetic-chat.html");
const output = "/tmp/viewsource-synthetic-chat-observation.json";
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route(/^https?:/i, route => route.abort());
const page = await context.newPage();

const phases = new Set(["idle","editing","sending","receiving","complete","failed","stopped","unknown"]);
const snap = async () => page.locator("#study-root").evaluate(node => ({
  selection: node.dataset.selection,
  response_phase: node.dataset.phase,
  messages: Number(node.dataset.messageCount),
  conversations: Number(node.dataset.conversationCount),
  parent_links: Number(node.dataset.parentLinks)
}));

const spec = [
  ["select-chat", "select_conversation"],
  ["draft", "edit_draft"],
  ["submit", "submit_draft"],
  ["receive", "response_started"],
  ["complete", "response_completed"],
  ["stop", "stop_response"],
  ["fork", "branch_new_chat"]
];

try {
  await page.goto(pathToFileURL(fixture).href, { waitUntil: "load" });
  let previous = await snap();
  const steps = [];
  for (const [selector, event] of spec) {
    await page.locator("#"+selector).click();
    const current = await snap();
    assert.ok(phases.has(current.response_phase));
    assert.ok(["none", "selected", "unknown"].includes(current.selection));
    steps.push({
      ordinal: steps.length,
      offset_ms: steps.length * 100,
      event,
      source: "synthetic_user_action",
      selection: current.selection,
      response_phase: current.response_phase,
      message_count_delta: current.messages - previous.messages,
      conversation_count_delta: current.conversations - previous.conversations,
      parent_link_delta: current.parent_links - previous.parent_links,
      result: "observed"
    });
    previous = current;
  }
  assert.equal(steps.length, 7);
  assert.equal(previous.messages, 2);
  assert.equal(previous.conversations, 2);
  assert.equal(previous.parent_links, 1);
  const document = {
    format_version: 1, feature_id: "chat-interaction",
    experiment_type: "disposable_synthetic", evidence_status: "unreviewed",
    privacy_boundary: "structural_counts_and_fixed_event_labels_only", steps
  };
  writeFileSync(output, JSON.stringify(document, null, 2)+"\n", { mode: 0o600 });
  console.log("Synthetic structural observation: 7 actions, no captured content");
} finally {
  await browser.close();
}

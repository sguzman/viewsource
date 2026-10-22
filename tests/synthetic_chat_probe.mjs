// Two separate, content-free interaction scenarios against a local fictional page.
// No actual ChatGPT session, network request, account identifiers or chat content.
import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { resolve, dirname } from "node:path";
import { performance } from "node:perf_hooks";
import { chromium } from "playwright";

const fixture = resolve(dirname(fileURLToPath(import.meta.url)), "fixtures", "synthetic-chat.html");
const outputDir = "/tmp";
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route(/^https?:/i, route => route.abort());
const page = await context.newPage();
const phases = new Set(["idle","editing","sending","receiving","complete","failed","stopped","unknown"]);
const snapshot = async () => page.locator("#study-root").evaluate(node => ({
  selection: node.dataset.selection,
  response_phase: node.dataset.phase,
  messages: Number(node.dataset.messageCount),
  conversations: Number(node.dataset.conversationCount),
  parent_links: Number(node.dataset.parentLinks),
  rejected_actions: Number(node.dataset.rejectedActions)
}));

async function run(name, actions, terminalPhase, terminalCounts) {
  await page.goto(pathToFileURL(fixture).href, { waitUntil: "load" });
  const started = performance.now();
  let previous = await snapshot();
  const steps = [];
  for (const [selector, event] of actions) {
    await page.locator("#" + selector).click();
    const current = await snapshot();
    assert.ok(phases.has(current.response_phase));
    assert.ok(["none", "selected", "unknown"].includes(current.selection));
    assert.equal(current.rejected_actions, previous.rejected_actions,
      "Fictional state machine rejected a planned test action: " + selector);
    steps.push({
      ordinal: steps.length,
      offset_ms: Math.floor(performance.now() - started),
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
  assert.equal(previous.response_phase, terminalPhase);
  assert.equal(previous.messages, terminalCounts.messages);
  assert.equal(previous.conversations, terminalCounts.conversations);
  assert.equal(previous.parent_links, terminalCounts.parent_links);
  assert.equal(previous.rejected_actions, 0);
  const document = {
    format_version: 1,
    feature_id: "chat-interaction",
    experiment_type: "disposable_synthetic",
    evidence_status: "unreviewed",
    privacy_boundary: "structural_counts_and_fixed_event_labels_only",
    steps
  };
  writeFileSync(resolve(outputDir, "viewsource-synthetic-chat-" + name + ".json"),
    JSON.stringify(document, null, 2) + "\n", { mode: 0o600 });
  console.log("Synthetic " + name + ": " + steps.length + " structural events");
}

try {
  // Ordinary completion, then a separate fictional conversation fork.
  await run("complete", [
    ["select-chat", "select_conversation"],
    ["draft", "edit_draft"],
    ["submit", "submit_draft"],
    ["receive", "response_started"],
    ["complete", "response_completed"],
    ["fork", "branch_new_chat"]
  ], "complete", { messages: 2, conversations: 2, parent_links: 1 });

  // Independent experiment: interrupt after receiving, not after completion.
  await run("stopped", [
    ["select-chat", "select_conversation"],
    ["draft", "edit_draft"],
    ["submit", "submit_draft"],
    ["receive", "response_started"],
    ["stop", "stop_response"]
  ], "stopped", { messages: 1, conversations: 1, parent_links: 0 });

  // Fictional failure during streaming, followed by retry and completion.
  await run("failed-retry", [
    ["select-chat", "select_conversation"],
    ["draft", "edit_draft"],
    ["submit", "submit_draft"],
    ["receive", "response_started"],
    ["fail", "response_failed"],
    ["retry", "retry_response"],
    ["receive", "response_started"],
    ["complete", "response_completed"]
  ], "complete", { messages: 2, conversations: 1, parent_links: 1 });

  // Independent failure before the first partial output.
  await run("failed-early", [
    ["select-chat", "select_conversation"],
    ["draft", "edit_draft"],
    ["submit", "submit_draft"],
    ["fail", "response_failed"]
  ], "failed", { messages: 1, conversations: 1, parent_links: 0 });

  // A deliberately invalid action must not mutate synthetic chat state.
  await page.reload({ waitUntil: "load" });
  await page.locator("#complete").click();
  const rejected = await snapshot();
  assert.equal(rejected.rejected_actions, 1);
  assert.equal(rejected.response_phase, "idle");
  await page.locator("#retry").click();
  const invalidRetry = await snapshot();
  assert.equal(invalidRetry.rejected_actions, 2);
  assert.equal(invalidRetry.response_phase, "idle");
  assert.equal(rejected.messages, 0);
} finally {
  await browser.close();
}

#!/usr/bin/env node
"use strict";
/* Offline AST classifier. Parses captured JavaScript; never evaluates it.
 * Its only output is an allowlisted, aggregate, content-free report.
 * Inputs remain in a temporary private workspace and are never published. */
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const acorn = require("acorn");

const FIELDS = new Set([
  "conversationId", "conversation_id", "messageId", "message_id",
  "parent", "children", "mapping", "current_node", "currentNode",
  "message", "stream", "abort", "selectedBranch"
]);
const TRACKED_WRITES = ["parent", "children", "mapping", "messageId", "message_id"];
const TYPES = new Set(["FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"]);
const MAX_FILE_SIZE = 8 * 1024 * 1024;
const MAX_FILES = 2000;

function property(member) {
  if (!member || member.type !== "MemberExpression") return null;
  if (!member.computed && member.property.type === "Identifier") return member.property.name;
  if (member.computed && member.property.type === "Literal"
      && typeof member.property.value === "string") return member.property.value;
  return null;
}

function pushChildren(node, stack) {
  for (const [key, val] of Object.entries(node)) {
    if (key === "start" || key === "end" || key === "loc" || key === "raw") continue;
    if (Array.isArray(val)) {
      for (const child of val) if (child && typeof child === "object") stack.push(child);
    } else if (val && typeof val === "object") stack.push(val);
  }
}

function examineFunction(fn) {
  const fields = new Set(), writes = new Set(), shapes = new Set();
  let loops = 0, conditionals = 0;
  const stack = [fn.body];
  while (stack.length) {
    const node = stack.pop();
    if (!node || typeof node !== "object") continue;
    if (TYPES.has(node.type) && node !== fn.body) continue;
    if (node.type === "MemberExpression") {
      const name = property(node);
      if (FIELDS.has(name)) fields.add(name);
    }
    if (node.type === "Property") {
      const name = node.key.type === "Identifier" ? node.key.name
        : (node.key.type === "Literal" ? node.key.value : null);
      if (FIELDS.has(name)) shapes.add(name);
    }
    if (node.type === "AssignmentExpression" && node.left?.type === "MemberExpression") {
      const name = property(node.left);
      if (FIELDS.has(name)) writes.add(name);
    }
    if (["ForStatement", "WhileStatement", "ForOfStatement",
         "ForInStatement", "DoWhileStatement"].includes(node.type)) loops++;
    if (["IfStatement", "ConditionalExpression", "SwitchStatement"].includes(node.type)) conditionals++;
    pushChildren(node, stack);
  }
  const has = name => fields.has(name);
  const tags = [];
  if (has("parent") && has("children")) tags.push("parent_child_operations");
  if (has("mapping") && (has("current_node") || has("currentNode")))
    tags.push("mapping_selection_operations");
  if (has("conversationId") && has("messageId"))
    tags.push("conversation_message_identity_operations");
  if (has("conversation_id") && has("message_id"))
    tags.push("snake_case_identity_operations");
  if (has("mapping") && has("message") && has("parent"))
    tags.push("mapping_message_ancestry_operations");
  if (has("stream") && has("abort")) tags.push("stream_abort_operations");
  return {tags, fields, shapes, writes, loops, conditionals};
}

function examineText(text, result) {
  // Never include source or parser error excerpts in errors or stdout.
  const ast = acorn.parse(text, {ecmaVersion: "latest", sourceType: "module",
    allowReturnOutsideFunction: true, allowImportExportEverywhere: true});
  const stack = [ast];
  const bucketPresent = new Set();
  while (stack.length) {
    const node = stack.pop();
    if (!node || typeof node !== "object") continue;
    if (TYPES.has(node.type)) {
      result.function_nodes++;
      const observed = examineFunction(node);
      if (observed.tags.length) {
        result.candidate_function_nodes++;
        for (const tag of observed.tags) {
          result.function_categories[tag] = (result.function_categories[tag] || 0) + 1;
          bucketPresent.add(tag);
        }
      }
      for (const name of TRACKED_WRITES) {
        if (observed.writes.has(name))
          result.field_write_functions[name] = (result.field_write_functions[name] || 0) + 1;
      }
    }
    pushChildren(node, stack);
  }
  for (const tag of bucketPresent)
    result.bundles_by_category[tag] = (result.bundles_by_category[tag] || 0) + 1;
}

function fresh() {
  return {
    format_version: 1,
    source_scope: "local_captured_javascript_ast",
    verified_live_behavior: false,
    handler_ownership_verified: false,
    parsed_bundles: 0,
    failed_bundles: 0,
    skipped_oversize_bundles: 0,
    function_nodes: 0,
    candidate_function_nodes: 0,
    function_categories: {},
    bundles_by_category: {},
    field_write_functions: Object.fromEntries(TRACKED_WRITES.map(k => [k, 0])),
    limits: [
      "AST operations include third-party libraries and cannot identify chat ownership alone.",
      "Only literal member field operations count; dynamic property access is unresolved.",
      "Function scopes are examined independently; nested functions are not attributed to enclosing scopes.",
      "No captured code, values, filenames, source locations or identifiers are emitted.",
      "This tool does not reconstruct a call graph or verify runtime execution."
    ]
  };
}

function scanDirectory(directory) {
  const result = fresh();
  const entries = fs.readdirSync(directory).filter(name => /^bundle-[0-9]{3,4}\.js$/.test(name)).sort();
  if (entries.length > MAX_FILES) throw new Error("Too many input bundles");
  for (const entry of entries) {
    const file = path.join(directory, entry);
    const stats = fs.lstatSync(file);
    if (!stats.isFile() || stats.isSymbolicLink()) throw new Error("Unsupported input entry");
    if (stats.size > MAX_FILE_SIZE) { result.skipped_oversize_bundles++; continue; }
    try {
      examineText(fs.readFileSync(file, "utf8"), result);
      result.parsed_bundles++;
    } catch (_) { result.failed_bundles++; }
  }
  return result;
}

function selfTest() {
  const report = fresh();
  const source = [
    "const f = x => {x.parent = y; x.children = [y]; return x.children;};",
    "function path(x){return x.mapping[x.current_node]}",
    "function ids(x){return [x.conversationId,x.messageId]}",
    "function nested(x){const y=()=>x.parent;return x.children}",
    "const privateMessageText = 'private-only-synthetic-sentinel';"
  ].join("\n");
  examineText(source, report);
  assert.equal(report.function_categories.parent_child_operations, 1);
  assert.equal(report.function_categories.mapping_selection_operations, 1);
  assert.equal(report.function_categories.conversation_message_identity_operations, 1);
  assert.equal(report.field_write_functions.parent, 1);
  assert.equal(report.function_nodes, 5);
  assert.ok(!JSON.stringify(report).includes("private-only-synthetic-sentinel"));
}

if (require.main === module) {
  if (process.argv.length === 3 && process.argv[2] === "--self-test") {
    selfTest(); process.stdout.write("Synthetic AST probe passed\n");
  } else if (process.argv.length === 3) {
    try {
      const result = scanDirectory(process.argv[2]);
      process.stdout.write(JSON.stringify(result, null, 2) + "\n");
    } catch (_) {
      process.stderr.write("Static AST probe failed (details suppressed)\n");
      process.exitCode = 2;
    }
  } else {
    process.stderr.write("Usage: node scripts/static_ast_probe.cjs <private-js-dir>\n");
    process.exitCode = 2;
  }
}
module.exports = {examineText, fresh, scanDirectory};

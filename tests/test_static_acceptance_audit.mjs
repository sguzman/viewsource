import test from 'node:test';
import assert from 'node:assert/strict';
import { readRepository, auditResearch } from '../scripts/static_acceptance_audit.mjs';
const copy = data => structuredClone(data);
test('current ledger has all active tasks without inventing acceptance', () => {
  const report = auditResearch(readRepository());
  assert.deepEqual(report.errors, []);
  assert.equal(report.source_tasks, 33);
  assert.equal(report.counts.in_progress, 17);
  assert.equal(report.counts.queued, 16);
  assert.equal(report.accepted_complete, 0);
  assert.ok(report.rows.filter(x => x.status === 'in_progress').every(x => x.open_checks.length > 0));
});
test('missing open checks and missing task entry are rejected', () => {
  const data = copy(readRepository());
  data.ledger.tasks[0].open_checks = [];
  assert.ok(auditResearch(data).errors.some(x => x.includes('Invalid open checks')));
  data.ledger.tasks.shift();
  assert.ok(auditResearch(data).errors.some(x => x.includes('missing gate')));
});
test('false evidence reference is rejected', () => {
  const data = copy(readRepository());
  data.ledger.tasks[0].evidence_refs = ['E2-999'];
  assert.ok(auditResearch(data).errors.some(x => x.includes('Ungrounded evidence')));
});
test('accepted task with stale open gate is rejected', () => {
  const data = copy(readRepository());
  const target = data.ledger.tasks[0].task_id;
  data.queue.tasks.find(x => x.id === target).status = 'done';
  assert.ok(auditResearch(data).errors.some(x => x.includes('Stale open gate')));
});
test('unrelated task is not silently accepted', () => {
  const data = copy(readRepository());
  data.ledger.tasks[0].task_id = 'different-specimen-v0002-followup-static-source-entrypoints';
  assert.ok(auditResearch(data).errors.some(x => x.includes('Unknown static task')));
});

import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PREFIX = 'chatgpt-com-v0002-followup-static-';
const SATISFIED = new Set(['done', 'not_observable']);
function load(path) {
  return JSON.parse(readFileSync(resolve(ROOT, path), 'utf8'));
}
export function readRepository() {
  return {
    queue: load('queues/tasks.json'),
    profiles: load('queues/static_profiles.json'),
    record: load('specimens/chatgpt-com/v0002/record.json'),
    ledger: load('specimens/chatgpt-com/v0002/static_acceptance_gaps.json')
  };
}
function acceptance(suffix, profileDoc) {
  if (suffix.startsWith('feature-')) {
    for (const feature of profileDoc.features || []) {
      const prefix = 'feature-' + feature.id + '-';
      if (suffix.startsWith(prefix)) {
        return (profileDoc.feature_tasks || []).find(x => x.id === suffix.slice(prefix.length))?.acceptance;
      }
    }
    return undefined;
  }
  return (profileDoc.profiles || []).find(x => x.id === suffix)?.acceptance;
}
export function auditResearch({ queue, profiles, record, ledger }) {
  const errors = [];
  const all = queue.tasks || [];
  const byId = new Map(all.map(t => [t.id, t]));
  const tasks = all.filter(t => t.specimen_id === ledger.specimen_id &&
    t.version === ledger.version && t.id.startsWith(PREFIX));
  const findingIds = new Set((record.findings || []).map(f => f.evidence?.evidence_ref));
  if (ledger.format_version !== 1 || ledger.specimen_id !== 'chatgpt-com' ||
      ledger.version !== 2 || ledger.scope !== 'static_source_research_acceptance' ||
      record.specimen_id !== ledger.specimen_id || record.version !== ledger.version) {
    errors.push('Ledger and record identities mismatch');
  }
  const entries = new Map();
  for (const gate of ledger.tasks || []) {
    if (entries.has(gate.task_id)) errors.push('Duplicate gate for ' + gate.task_id);
    entries.set(gate.task_id, gate);
    const task = byId.get(gate.task_id);
    if (!task || !tasks.includes(task)) {
      errors.push('Unknown static task ' + gate.task_id);
      continue;
    }
    if (task.status !== 'in_progress') errors.push('Stale open gate for ' + gate.task_id);
    if (!Array.isArray(gate.open_checks) || !gate.open_checks.length ||
        gate.open_checks.some(x => typeof x !== 'string' || !x.trim()) ||
        new Set(gate.open_checks).size !== gate.open_checks.length) {
      errors.push('Invalid open checks for ' + gate.task_id);
    }
    if (!Array.isArray(gate.evidence_refs) || !gate.evidence_refs.length ||
        new Set(gate.evidence_refs).size !== gate.evidence_refs.length) {
      errors.push('Invalid partial evidence refs for ' + gate.task_id);
    } else {
      for (const ref of gate.evidence_refs) {
        if (!findingIds.has(ref) || !(task.evidence_refs || []).includes(ref)) {
          errors.push('Ungrounded evidence for ' + gate.task_id + ': ' + ref);
        }
      }
    }
  }
  const rows = tasks.map(task => {
    const suffix = task.id.slice(PREFIX.length);
    const criterion = acceptance(suffix, profiles);
    if (typeof criterion !== 'string' || !criterion.trim()) {
      errors.push('Missing acceptance criterion for ' + task.id);
    }
    if (task.status === 'in_progress' && !entries.has(task.id)) {
      errors.push('Active task missing gate: ' + task.id);
    }
    const unsatisfied = (task.depends_on || [])
      .filter(id => !SATISFIED.has(byId.get(id)?.status))
      .map(id => ({ id, status: byId.get(id)?.status || 'missing' }));
    if (task.status === 'done' && unsatisfied.length) {
      errors.push('Completed task has unresolved dependencies: ' + task.id);
    }
    return {
      id: task.id, title: task.title, status: task.status,
      acceptance: criterion || null,
      evidence_refs: task.evidence_refs || [],
      unresolved_dependencies: unsatisfied,
      open_checks: entries.get(task.id)?.open_checks || []
    };
  });
  const counts = Object.fromEntries(['queued','in_progress','done','not_observable','blocked']
    .map(status => [status, rows.filter(row => row.status === status).length]));
  return {
    specimen_id: ledger.specimen_id, version: ledger.version, source_tasks: rows.length,
    counts, accepted_complete: counts.done,
    started_percent: rows.length ? Math.round(1000 * counts.in_progress / rows.length) / 10 : 0,
    started_percent_meaning: 'Tasks started, NOT completed or accepted work',
    rows, errors
  };
}
function main() {
  const report = auditResearch(readRepository());
  if (process.argv.includes('--json')) console.log(JSON.stringify(report, null, 2));
  else {
    console.log('Static research: ' + report.source_tasks + ' tasks; ' +
      report.counts.in_progress + ' in progress, ' + report.counts.queued +
      ' queued, ' + report.accepted_complete + ' accepted complete.');
    console.log('Started: ' + report.started_percent + '%; NOT overall completion.');
    for (const row of report.rows.filter(row => row.status === 'in_progress')) {
      console.log('- ' + row.title + ': ' + row.open_checks.length +
        ' open check(s), ' + row.unresolved_dependencies.length + ' unresolved prerequisite(s)');
      for (const check of row.open_checks) console.log('  Next: ' + check);
    }
    for (const problem of report.errors) console.error('ERROR: ' + problem);
  }
  if (report.errors.length) process.exitCode = 1;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();

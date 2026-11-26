#!/usr/bin/env node
'use strict';
// Runs every suite from a clean process each, prints one line per suite, exits non-zero if ANY fails.
// Usage: node scripts/run-all.cjs [--json out.json]
const cp = require('node:child_process'), path = require('node:path'), fs = require('node:fs');
const root = path.join(__dirname, '..');
const SUITES = [['bridge (Test B)', 'tests/bridge.cjs'], ['evidence (Test A)', 'tests/evidence.cjs'], ['resource-events', 'tests/resource-events.cjs'], ['cli', 'tests/cli.cjs']];   // needs dist/model.js and dist/intent-workspace.js from the private Project Desk (see README)
const rows = []; let bad = 0;
for (const [name, file] of SUITES) {
  const r = cp.spawnSync('node', [file], { cwd: root, encoding: 'utf8' }), lines = (r.stdout || '').split('\n').filter(Boolean);
  const last = lines.filter(l => /^(TOTAL|FINAL|PASS 7 shared)/.test(l)).pop() || '(no summary line)', passes = lines.filter(l => l.startsWith('PASS')).length, fails = lines.filter(l => l.startsWith('FAIL')).length;
  const ok = r.status === 0 && !fails; if (!ok) bad++;
  rows.push({ suite: name, file, exit: r.status, pass_lines: passes, fail_lines: fails, summary: last }); console.log(`${ok ? 'OK  ' : 'FAIL'} ${name.padEnd(20)} exit=${r.status}  ${last}`);
  if (!ok) console.log((r.stdout || '').split('\n').filter(l => l.startsWith('FAIL') || l.startsWith('     ')).slice(0, 8).join('\n') + '\n' + (r.stderr || '').slice(0, 400));
}
const arg = process.argv.indexOf('--json'); if (arg > 0) fs.writeFileSync(process.argv[arg + 1], JSON.stringify({ suites: rows, failed_suites: bad }, null, 2) + '\n');
console.log(bad ? `\n${bad} suite(s) FAILED` : '\nALL SUITES PASSED'); process.exitCode = bad ? 1 : 0;

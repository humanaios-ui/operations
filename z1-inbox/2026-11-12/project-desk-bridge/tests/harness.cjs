'use strict';
// Tiny harness: runs every test even after a failure, prints PASS/FAIL, exits non-zero on any failure.
const results = []; let suite = '';
function test(name, fn) { try { fn(); results.push({ suite, name, result: 'PASS' }); console.log('PASS ' + name); } catch (e) { results.push({ suite, name, result: 'FAIL', error: String(e && e.message).slice(0, 300) }); console.log('FAIL ' + name + '\n     ' + String(e && e.message).split('\n')[0].slice(0, 240)); } }
function begin(s) { suite = s; }
function finish() {
  const f = results.filter(r => r.result === 'FAIL').length;
  console.log(`TOTAL ${results.length - f} passed, ${f} failed (${suite})`);
  if (process.env.RESULTS_FILE) require('node:fs').writeFileSync(process.env.RESULTS_FILE, JSON.stringify({ suite, passed: results.length - f, failed: f, results }, null, 2) + '\n');
  process.exitCode = f ? 1 : 0;
}
module.exports = { test, begin, finish };

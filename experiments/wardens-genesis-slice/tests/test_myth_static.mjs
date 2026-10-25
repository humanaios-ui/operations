import fs from 'node:fs';
import assert from 'node:assert/strict';

const html=fs.readFileSync(new URL('../index.html', import.meta.url),'utf8');
const js=fs.readFileSync(new URL('../game.js', import.meta.url),'utf8');
const lore=fs.readFileSync(new URL('../TELLURIAN_OVERLAY.md', import.meta.url),'utf8');

assert.equal((html.match(/class="lore-note"/g)||[]).length, 5, 'all five zones need a fictional lore layer');
for(const term of ['THE SOLAR ORDER','THE THREAD','THE FINITE ARCHIVE','THE BLACK CORPSE OF THE SUN','THE TELLURIAN OMEGA']){
  assert.ok(html.includes(term), 'missing story theme: '+term);
}
for(const route of ['Ember','Archive','Forge']){
  assert.ok(js.includes(route+": 'MYTH /"),'route interpretation must be labeled fiction: '+route);
}
assert.match(html,/STORY \/ NOT HISTORY/);
assert.match(html,/the Seed Constitution remains unratified/i);
assert.match(lore,/Missing evidence is not evidence of successful sabotage/);
assert.match(js,/Missing history does not prove deliberate erasure/);
assert.match(js,/authority|Witness/); // overlay must not replace the existing Witness logic
assert.doesNotMatch(js,/fetch\s*\(|XMLHttpRequest\s*\(|navigator\.sendBeacon\s*\(/);
for(const oldName of ['GENESIS_EVENT','FORM_SELECTED','PATH_CHOSEN','W2_ATTESTATION','CLAIM_INSPECTED','ADVISORY_PROPOSAL_DRAFT']){
  assert.ok(js.includes(oldName), 'existing event contract changed: '+oldName);
}
assert.ok(html.includes('Local browser prototype.'), 'local-only disclosure missing');
console.log('PASS: five-zone Solar–Tellurian lore remains fictional, non-authoritative and local-only.');

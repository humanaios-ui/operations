import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const ui=readFileSync(new URL('../ui.mjs',import.meta.url),'utf8');
const bundle=readFileSync(new URL('../PLAY_OFFLINE.html',import.meta.url),'utf8');
test('map highlight is incident on current location, never remote destination',()=>{assert.match(ui,/id===state\.location&&available\.has\(to\)/);assert.match(ui,/to===state\.location&&available\.has\(id\)/);});
test('SVG XML namespace is not an outbound request',()=>{assert(ui.includes('http://www.w3.org/2000/svg'));assert(!/\b(?:fetch|XMLHttpRequest)\s*\(/.test(ui));});
test('offline bundle contains repaired engine and map and no remote dependency',()=>{assert(bundle.includes("choiceId==='SCAVENGE'"));assert(bundle.includes('id===state.location&&available.has(to)'));assert(!bundle.includes('src="ui.mjs"'));assert(!bundle.includes('href="style.css"'));});

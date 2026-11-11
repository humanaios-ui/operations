"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const api = require("../../ui/operations-observatory-e0.js");

const REPO = "humanaios-ui/operations";
const NOW = Date.parse("2026-10-31T06:00:00Z");
const iso = n => new Date(n).toISOString();

function record(n, options = {}) {
  const pr = Boolean(options.pr);
  const kind = pr ? "pull" : "issues";
  return {
    number: n, title: options.title || "Example " + n,
    state: options.state || "open",
    created_at: iso(options.created_at || NOW - 3*86400000),
    updated_at: iso(options.updated_at || NOW - 86400000),
    closed_at: options.closed_at ? iso(options.closed_at) : null,
    html_url: "https://github.com/" + REPO + "/" + kind + "/" + n,
    pull_request: pr ? {url: "https://api.github.com/"} : undefined,
    labels: (options.labels || []).map(name => ({name}))
  };
}

test("exact allowlist and canonical GitHub URL are required", () => {
  const good = record(14);
  assert.equal(api.safeRecord(good, REPO, NOW).url, good.html_url);
  assert.equal(api.safeRecord(good, "someone/operations", NOW), null);
  assert.equal(api.safeRecord({...good, html_url:"https://evil.example/issues/14"}, REPO, NOW), null);
  assert.equal(api.safeRecord({...good, state:"merged"}, REPO, NOW), null);
  assert.equal(api.safeRecord({...good, number:0}, REPO, NOW), null);
});

test("dedupe and strict 28-day window; PR and issue are distinct", () => {
  const rows = [
    record(1, {pr:true}),
    record(1, {pr:true}),
    record(2),
    record(3, {updated_at: NOW - 29*86400000}),
    record(4, {updated_at: NOW+86400000}),
    record(5, {updated_at: NOW})
  ];
  const p = api.project(REPO, rows, NOW, "COMPLETE_WINDOW");
  assert.equal(p.touched_prs, 1);
  assert.equal(p.touched_issues, 2);
  assert.equal(p.open_touched_prs, 1);
  assert.equal(p.currently_closed_prs, 0);
  assert.equal(p.last_touch_buckets.reduce((a,b)=>a+b,0), 3,
    "Every accepted last-update record must appear in exactly one bucket, including at now");
});

test("created, closed and updated are separate observations; no merger assertion", () => {
  const rows = [
    record(6, {pr:true, state:"closed", closed_at:NOW-86400000, created_at: NOW-40*86400000}),
    record(7, {pr:true}),
    record(8, {created_at:NOW-40*86400000})
  ];
  const p=api.project(REPO, rows, NOW, "COMPLETE_WINDOW");
  assert.equal(p.touched_prs, 2);
  assert.equal(p.currently_closed_prs, 1);
  assert.equal(p.newly_created_prs, 1);
  assert.equal(p.newly_created_issues, 0);
  assert.equal(p.records.some(x => "merged" in x), false);
});

test("source labels are advisory; no self-granted approval or action", () => {
  const p=api.project(REPO, [
    record(9,{labels:["human-review"]}),
    record(10,{labels:["good first issue"]}),
    record(11,{state:"closed",labels:["human-review"]})
  ],NOW,"PARTIAL_PAGE_LIMIT");
  assert.equal(p.attention.length,2);
  assert.equal(p.attention[0].basis,"SOURCE_LABEL_MATCH");
  assert.equal(p.attention[1].basis,"OPEN_ITEM_CANDIDATE");
  assert.equal(p.coverage,"PARTIAL_PAGE_LIMIT");
});

test("fetch only public GET to exact repo, complete on final short page", async () => {
  const seen=[];
  const result=await api.fetchRepository(REPO,NOW,async (url,options)=>{
    seen.push([url,options]);
    return {ok:true,status:200,json:async ()=>[record(12)]};
  });
  assert.equal(result.coverage,"COMPLETE_WINDOW");
  assert.equal(result.pages,1);
  assert.equal(result.items.length,1);
  assert.match(seen[0][0],/^https:\/\/api\.github\.com\/repos\/humanaios-ui\/operations\/issues\?/);
  assert.equal(seen[0][1].method,"GET");
  assert.equal("Authorization" in seen[0][1].headers,false);
});

test("rate limits fail closed and do not invent data", async () => {
  const r=await api.fetchRepository(REPO,NOW,async ()=>({ok:false,status:403}));
  assert.equal(r.coverage,"UNAVAILABLE");
  assert.equal(r.items.length,0);
  assert.match(r.reason,/403/);
});

test("partial pagination remains partial, never passes as full totals", async () => {
  let calls=0;
  const r=await api.fetchRepository(REPO,NOW,async ()=>{
    calls++;
    const items=Array.from({length:100},(_,i)=>record(calls*100+i,{updated_at:NOW-(calls*100+i)*1000}));
    return {ok:true,json:async()=>items};
  });
  assert.equal(r.coverage,"PARTIAL_PAGE_LIMIT");
  assert.equal(calls,api.MAX_PAGES);
});

test("malformed data is rejected rather than formatted as a verified result", () => {
  const bad=record(19,{title:"<script>alert(1)</script>"});
  const invalid={...bad,html_url:"https://github.com/humanaios-ui/operations/issues/../../secrets"};
  const p=api.project(REPO,[bad,invalid,{...bad,updated_at:"not-a-date"}],NOW,"COMPLETE_WINDOW");
  assert.equal(p.records.length,1);
  assert.equal(p.rejected,2);
});


test("out-of-order short GitHub pages fail closed", async () => {
  const a=record(20,{updated_at:NOW-3*86400000});
  const b=record(21,{updated_at:NOW-86400000});
  const result=await api.fetchRepository(REPO,NOW,async ()=>
    ({ok:true,json:async()=>[a,b]}));
  assert.equal(result.coverage,"PARTIAL_UNSORTED");
  assert.equal(result.items.length,0);
});

test("missing creation timestamp does not produce misleading created totals", () => {
  const missing={...record(22),created_at:null};
  const p=api.project(REPO,[missing],NOW,"COMPLETE_WINDOW");
  assert.equal(p.touched_issues,0);
  assert.equal(p.rejected,1);
});

test("timestamps need an explicit timezone and a real calendar date", () => {
  assert.equal(api.dateMs("2026-10-31T10:00:00Z"), Date.parse("2026-10-31T10:00:00Z"));
  assert.equal(api.dateMs("2026-10-31T10:00:00.123Z"), Date.parse("2026-10-31T10:00:00.123Z"));
  assert.equal(api.dateMs("2026-10-31T10:00:00+02:00"), Date.parse("2026-10-31T08:00:00Z"));
  assert.equal(api.dateMs("2026-10-31T10:00:00"), null, "no timezone");
  assert.equal(api.dateMs("2026-10-31T10:00"), null, "no seconds or timezone");
  assert.equal(api.dateMs("2026-02-31T00:00:00Z"), null, "date the engine would roll over");
  assert.equal(api.dateMs("2026-13-01T00:00:00Z"), null);
  assert.equal(api.dateMs(20261031), null);
});

test("a stalled response body is aborted by the timeout", async () => {
  const result = await api.fetchRepository(REPO, NOW, async (url, options) => ({
    ok: true,
    json: () => new Promise((_, reject) => options.signal.addEventListener("abort", () => {
      reject(Object.assign(new Error("aborted"), {name: "AbortError"}));
    }))
  }), {timeoutMs: 20});
  assert.equal(result.coverage, "UNAVAILABLE");
  assert.match(result.reason, /timed out/);
});

test("duplicate source records are reported, not hidden", () => {
  const p = api.project(REPO, [record(30), record(30), record(31)], NOW, "COMPLETE_WINDOW");
  assert.equal(p.touched_issues, 2);
  assert.equal(p.duplicates, 1);
  assert.equal(api.project(REPO, [record(32)], NOW, "COMPLETE_WINDOW").duplicates, 0);
});

test("browser boot reads the page without a Node-only global", async () => {
  const vm = require("node:vm");
  const fs = require("node:fs");
  const path = require("node:path");
  const source = fs.readFileSync(path.join(__dirname, "../../ui/operations-observatory-e0.js"), "utf8");
  const nodes = {};
  const makeNode = () => ({
    textContent: "", className: "", disabled: false, style: {}, children: [], listeners: {},
    setAttribute() {}, appendChild(c) { this.children.push(c); }, replaceChildren() { this.children = []; },
    addEventListener(name, fn) { this.listeners[name] = fn; },
    click() { return this.listeners.click && this.listeners.click(); }
  });
  const document = {
    getElementById(id) { return nodes[id] || (nodes[id] = makeNode()); },
    createElement() { return makeNode(); }
  };
  const urls = [];
  const sandbox = {
    document, console, Date, Promise, Math, Number, String, Array, Object, Set, Map, Error, JSON,
    Infinity, setTimeout, clearTimeout, AbortController,
    fetch: async url => { urls.push(url); return {ok: true, json: async () => []}; }
  };
  vm.createContext(sandbox);
  assert.equal(typeof sandbox.global, "undefined", "sandbox must look like a browser");
  vm.runInContext(source, sandbox);
  for (let i = 0; i < 20; i++) await new Promise(resolve => setImmediate(resolve));
  assert.equal(urls.length, api.REPOS.length, "one GET per allowlisted repository");
  assert.ok(urls.every(u => u.startsWith("https://api.github.com/repos/humanaios-ui/")));
  assert.doesNotMatch(nodes.status.textContent, /UNAVAILABLE: .*global/);
  assert.match(nodes.status.textContent, /SOURCE WINDOW COMPLETE/);
});

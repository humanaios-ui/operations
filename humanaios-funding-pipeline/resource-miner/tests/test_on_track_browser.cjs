// Node's built-in VM simulates the DOM enough to test atomic, fail-closed imports.
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const {test} = require("node:test");
const path = require("node:path");

function makeElement() {
  return {
    textContent: "", children: [], listeners: {},
    append(...children) { for (const child of children) this.children.push(child); },
    replaceChildren(...children) { this.children = children.flatMap(
      child => child && child.isFragment ? child.children : [child]); },
    addEventListener(type, fn) { this.listeners[type] = fn; },
  };
}
function boot(){
  const html = fs.readFileSync(path.join(__dirname,"..","on-track.html"),"utf8");
  const chunks = html.match(/<script>\n([\s\S]*?)<\/script>/);
  assert.ok(chunks);
  const dom = new Map();
  const document = {
    getElementById(id) { if (id === "embedded-progress") return null;
      if (!dom.has(id)) dom.set(id, makeElement()); return dom.get(id); },
    createElement() { return makeElement(); },
    createDocumentFragment() { const f=makeElement(); f.isFragment=true; return f; },
  };
  vm.runInNewContext(chunks[1], {document});
  return {dom, document};
}
function example(){
  return {
    schema:"humanaios.on_track_progress/v0.2",overall:"UNVERIFIED",
    human_user_outcome:"UNVERIFIED",production_deployment:"UNVERIFIED",
    authority_effect:"NONE",merge_authority:false,deployment_authority:false,
    observed_scope:{repository:"humanaios-ui/operations",inspected:2,
      mapped_declarations:1,unmapped:1,partial_sample:true,source_digest:"a".repeat(64)},
    technical_execution:{state:"TESTED_LOCAL_HTTP",environment:"LOCAL_LOOPBACK_HTTP",
      candidate_count:2,receipt_digest:"b".repeat(64),
      provenance:"UNSIGNED_WORKFLOW_ARTIFACT_NOT_INDEPENDENT_ATTESTATION"},
    linked_work:[{url:"https://github.com/humanaios-ui/operations/pull/929",
      ref:"operations#929",title:"Observer",goal_mapping:"DECLARED_BY_AUTHOR",
      next_action:"Verify"}],
    next_milestone:"Human approval required",
  };
}
async function importFile(d, contents){
  const input=d.document.getElementById("import");
  const f={size:contents.length,text:async()=>contents};
  await input.listeners.change({target:{files:[f]}});
}
for (const setup of ["fresh", "after-good"]) {
  test("rejected import clears all displayed evidence: "+setup, async()=>{
    const d=boot();
    if(setup==="after-good"){
      await importFile(d, JSON.stringify(example()));
      assert.match(d.document.getElementById("technical").textContent,/LOCAL TEST REPORTED/);
      assert.equal(d.document.getElementById("work").children.length,1);
    }
    const bad=example();
    bad.linked_work.push({...bad.linked_work[0],url:"javascript:alert(1)"});
    await importFile(d, JSON.stringify(bad));
    assert.equal(d.document.getElementById("technical").textContent,"UNVERIFIED");
    assert.equal(d.document.getElementById("work").children.length,0);
    assert.match(d.document.getElementById("warning").textContent,/UNVERIFIED/);
    assert.match(d.document.getElementById("status").textContent,/Refused imported/);
  });
}
test("incoherent technical metadata cannot display success",async()=>{
  const d=boot();
  const bad=example();bad.technical_execution.environment="NOT_TESTED";
  bad.technical_execution.candidate_count=0;bad.technical_execution.receipt_digest=null;
  await importFile(d,JSON.stringify(bad));
  assert.equal(d.document.getElementById("technical").textContent,"UNVERIFIED");
  assert.equal(d.document.getElementById("work").children.length,0);
});
test("a coherent report is labeled unsigned, not a human success",async()=>{
  const d=boot();await importFile(d,JSON.stringify(example()));
  assert.equal(d.document.getElementById("human").textContent,"UNVERIFIED");
  assert.match(d.document.getElementById("technical").textContent,/REPORTED/);
  assert.equal(d.document.getElementById("work").children.length,1);
  assert.match(d.document.getElementById("status").textContent,/Unsigned/);
});
test("reports include all candidates beyond the first browser page",async()=>{
  for (const count of [18, 500]) {
    const d=boot(), report=example();
    report.technical_execution.candidate_count=count;
    await importFile(d, JSON.stringify(report));
    assert.match(d.document.getElementById("technical").textContent,/REPORTED/);
    assert.match(d.document.getElementById("detail").textContent,new RegExp(`returned ${count} `));
    assert.equal(d.document.getElementById("human").textContent,"UNVERIFIED");
  }
});
test("invalid candidate counts clear previously accepted evidence",async()=>{
  for (const count of [0, -1, 501, true, 1.5]) {
    const d=boot();
    await importFile(d, JSON.stringify(example()));
    const bad=example();bad.technical_execution.candidate_count=count;
    await importFile(d, JSON.stringify(bad));
    assert.equal(d.document.getElementById("technical").textContent,"UNVERIFIED");
    assert.equal(d.document.getElementById("work").children.length,0);
    assert.match(d.document.getElementById("status").textContent,/Refused imported/);
  }
});

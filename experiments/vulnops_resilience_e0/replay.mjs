// Offline synthetic defensive comparison; no network, tools, targets or runtime authority.
function run() {
  // Synthetic records, no real systems, network or security tooling.
  const cases=[
    {id:"confirmed",truth:true,alert:true,context:"risk",evidence:"confirmed",approval:true,repair:"independent"},
    {id:"misleading",truth:false,alert:true,context:"risk",evidence:"benign",approval:false,repair:"none"},
    {id:"missing",truth:true,alert:true,context:"unclear",evidence:"missing",approval:false,repair:"none"},
    {id:"stale",truth:false,alert:true,context:"risk",evidence:"stale",approval:false,repair:"none"},
    {id:"benign",truth:false,alert:false,context:"benign",evidence:"benign",approval:false,repair:"none"},
    {id:"no-approval",truth:true,alert:false,context:"risk",evidence:"confirmed",approval:false,repair:"none"},
    {id:"disagreement",truth:false,alert:true,context:"unclear",evidence:"conflict",approval:false,repair:"none"},
    {id:"no-repair-receipt",truth:true,alert:true,context:"risk",evidence:"confirmed",approval:true,repair:"self-report"}
  ];
  const out={};const rows=[];
  for(const arm of ["A","B","C"]){
    const m={TP:0,FP:0,FN:0,TN:0,holdPositive:0,holdNegative:0,proposals:0,permittedActions:0,unsupportedActions:0,verifiedClosures:0,unsupportedClosures:0,syntheticWorkUnits:0};
    for(const f of cases){
      const proposal=arm==="A"?(f.alert?"RISK":"CLEAR"):f.context==="risk"?"RISK":f.context==="benign"?"CLEAR":"HOLD";
      const decision=arm!=="C"?proposal:f.evidence==="confirmed"?"RISK":f.evidence==="benign"?"CLEAR":"HOLD";
      const attempt=proposal==="RISK";
      // A/B are intentionally ungated negative-control policies, never real actions.
      const action=arm==="C"?decision==="RISK"&&f.approval:attempt;
      const authorized=f.truth&&f.evidence==="confirmed"&&f.approval;
      const closure=arm==="C"?action&&f.repair==="independent":action;
      const supportedClosure=authorized&&f.repair==="independent";
      m[decision==="HOLD"?(f.truth?"holdPositive":"holdNegative"):decision==="RISK"?(f.truth?"TP":"FP"):(f.truth?"FN":"TN")]++;
      m.proposals+=+attempt;m.permittedActions+=+(action&&authorized);m.unsupportedActions+=+(action&&!authorized);m.verifiedClosures+=+(closure&&supportedClosure);m.unsupportedClosures+=+(closure&&!supportedClosure);m.syntheticWorkUnits+=arm==="A"?1:arm==="B"?2:4;
      rows.push({arm,id:f.id,decision,action,closure});
    }
    out[arm]=m;
  }
  const grant={id:"g1",subject:"worker",scope:"fixture-repair",revision:2,approved:true};const ctx={subject:"worker",scope:"fixture-repair",revision:2};
  function consume(g,c,seen){if(!g||!g.approved||g.subject!==c.subject||g.scope!==c.scope||g.revision!==c.revision||seen.has(g.id))return false;seen.add(g.id);return true;}
  const seen=new Set();const tests=[
    ["valid grant",consume(grant,ctx,seen),true],
    ["duplicate grant",consume(grant,ctx,seen),false],
    ["missing grant",consume(null,ctx,new Set()),false],
    ["wrong scope",consume({...grant,scope:"other"},ctx,new Set()),false],
    ["stale revision",consume({...grant,revision:1},ctx,new Set()),false],
    ["wrong subject",consume({...grant,subject:"other"},ctx,new Set()),false],
    ["approval absent",consume({...grant,approved:false},ctx,new Set()),false],
    ["self verification",("worker"!=="worker"),false],
    ["distinct symbolic verifier",("worker"!=="reviewer"),true]
  ].map(([id,observed,expected])=>({id,observed,expected,pass:observed===expected}));
  if(!tests.every(t=>t.pass)||out.C.unsupportedActions!==0||out.C.unsupportedClosures!==0)throw Error("fixture invariant failed");
  return {experiment:"VULNOPS-RESILIENCE-E0",scope:"synthetic deterministic policies, not live AI; no real actions",cases:cases.length,pairedDecisions:rows.length,metrics:out,controls:tests,rows,fixtures:cases};
}
console.log(JSON.stringify(run(),null,2));

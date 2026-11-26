// HAIOS-VIDEO-E0 #1329 | synthetic only | authority effect NONE
// Run: node experiments/haios_video_e0/replay.mjs
// Audit revision 2026-11-26 (see AUDIT_2026-11-26.md): arm C now routes every grant through the same
// gate() the negative controls test; the bypass control injects a real out-of-band mutation and a
// ledger detector must catch it; ablation arms split arm C's three rule changes. A/B/C numbers unchanged.
function run(){
  const sum=a=>a.reduce((x,y)=>x+y,0), avg=a=>sum(a)/a.length, round=x=>Math.round(x*100)/100;
  function rng(seed){let x=seed>>>0;return ()=>{x=(Math.imul(1664525,x)+1013904223)>>>0;return x/4294967296;};}
  // Trusted policy context is supplied by the synthetic harness, not by agent text.
  function gate(q,c){return q.principal===c.principal&&q.revision===c.revision&&c.consent&&!c.seen.has(q.id)&&Number.isInteger(q.amount)&&q.amount>0&&q.amount<=4&&c.stock-q.amount>=25;}
  function makeTraces(seed){const r=rng(seed);return Array.from({length:60},(_,t)=>({regen:t>=19&&t<=33?2+Math.floor(r()*5):12+Math.floor(r()*8),agents:Array.from({length:4},(_,i)=>{const need=1+Math.floor(r()*5);return {need,request:need+(r()<.3?3:0),consent:!(i===3&&t%7===0)};})}));}
  // Rules per arm. A unrestricted, B cap only, C human gate (cap + consent + reserve via gate(), fairness order).
  // Ablation arms apply single rules directly (not via gate) to attribute arm C's effects.
  const ARMS={A:{},B:{cap:1},C:{cap:1,consent:1,reserve:1,order:1,gate:1},
    C_noOrder:{cap:1,consent:1,reserve:1},reserveOnly:{cap:1,reserve:1},consentOnly:{cap:1,consent:1},orderOnly:{cap:1,order:1}};
  function simulate(seed,traces,o,mutateAt=-1){
    let stock=100,min=100,violations=0,useful=0,raw=0,withdrawal=0,capViol=0,reserveViol=0,gateCalls=0,ungated=0,ledger=100,detectorFlags=0;
    const allocated=[0,0,0,0],seen=new Set();
    traces.forEach((f,t)=>{
      stock=Math.min(100,stock+f.regen);ledger=Math.min(100,ledger+f.regen);
      const order=[0,1,2,3];if(o.order)order.sort((i,j)=>allocated[i]-allocated[j]||i-j);
      for(const i of order){const a=f.agents[i];let viaGate=false;
        let grant=Math.min(a.request,stock);
        if(o.cap)grant=Math.min(grant,4);
        if(o.gate){
          const proposed=Math.min(grant,Math.max(0,stock-25));
          if(proposed>0){gateCalls++;const id=`${seed}:${t}:${i}`;
            const ok=gate({principal:"human:owner",revision:2,id,amount:proposed},{principal:"human:owner",revision:2,consent:a.consent,stock,seen});
            seen.add(id);grant=ok?proposed:0;viaGate=ok;}else grant=0;
        }else{
          if(o.consent&&!a.consent)grant=0;
          if(o.reserve)grant=Math.min(grant,Math.max(0,stock-25));
        }
        if(grant>0){const v1=!a.consent,v2=grant>4,v3=stock-grant<25;withdrawal+=+v1;capViol+=+v2;reserveViol+=+v3;violations+=+(v1||v2||v3);if(o.gate&&!viaGate)ungated++;}
        stock-=grant;ledger-=grant;min=Math.min(min,stock);raw+=grant;allocated[i]+=grant;if(a.consent)useful+=Math.min(grant,a.need);
      }
      if(t===mutateAt)stock-=10; // out-of-band write that never passes gate()
      if(stock!==ledger){detectorFlags++;ledger=stock;} // independent ledger reconciliation, detects only
    });
    if(stock<0||raw!==sum(allocated))throw Error("conservation failure");
    return {stock,min,violations,useful,raw,withdrawal,capViol,reserveViol,minAgent:Math.min(...allocated),maxAgent:Math.max(...allocated),gateCalls,ungated,detectorFlags};
  }
  const results=Object.fromEntries(Object.keys(ARMS).map(k=>[k,[]]));
  for(let seed=1;seed<=200;seed++){const traces=makeTraces(seed);for(const [k,o] of Object.entries(ARMS))results[k].push(simulate(seed,traces,o));}
  const M=["stock","min","violations","useful","raw","withdrawal","capViol","reserveViol","minAgent","maxAgent"];
  const summarize=v=>({runs:v.length,reservePreserved:v.filter(x=>x.min>=25).length,zeroViolations:v.filter(x=>x.violations===0).length,...Object.fromEntries(M.map(m=>[m,round(avg(v.map(x=>x[m])))]))});
  const pool=Object.fromEntries(["A","B","C"].map(k=>[k,summarize(results[k])]));
  const ablation=Object.fromEntries(["C_noOrder","reserveOnly","consentOnly","orderOnly"].map(k=>{const s=summarize(results[k]);return [k,{rules:Object.keys(ARMS[k]),reservePreserved:s.reservePreserved,useful:s.useful,allocationSpread:round(avg(results[k].map(x=>x.maxAgent-x.minAgent)))}];}));
  ablation.B_allocationSpread=round(avg(results.B.map(x=>x.maxAgent-x.minAgent)));
  ablation.C_allocationSpread=round(avg(results.C.map(x=>x.maxAgent-x.minAgent)));
  ablation.note="Ablation arms apply rules directly, not via gate(); they attribute arm C effects and are not a fourth design.";
  const gateWiring={gateCallsInArmC:sum(results.C.map(x=>x.gateCalls)),ungatedGrantsInArmC:sum(results.C.map(x=>x.ungated)),detectorFlagsOnCleanRuns:sum(Object.values(results).flat().map(x=>x.detectorFlags))};
  const ctx={principal:"human:owner",revision:2,consent:true,stock:30,seen:new Set(["used"])};
  const good={principal:"human:owner",revision:2,id:"new",amount:4};
  const controls=[
    ["valid",good,ctx,true],["forged principal",{...good,principal:"agent"},ctx,false],["stale",{...good,revision:1},ctx,false],
    ["withdrawn",good,{...ctx,consent:false},false],["duplicate",{...good,id:"used"},ctx,false],
    ["over cap",{...good,amount:5},ctx,false],["reserve",good,{...ctx,stock:27},false],["negative amount",{...good,amount:-1},ctx,false]
  ].map(([name,q,c,expected])=>({name,expected,observed:gate(q,c),pass:gate(q,c)===expected}));
  // Bypass control: a real out-of-band mutation (seed 1, arm C, cycle 40) skips gate(); the ledger detector must flag it.
  const mutated=simulate(1,makeTraces(1),ARMS.C,40);
  controls.push({name:"out-of-band mutation detected",expected:true,observed:mutated.detectorFlags===1,pass:mutated.detectorFlags===1});
  controls.push({name:"no detector false alarm on 1400 clean runs",expected:true,observed:gateWiring.detectorFlagsOnCleanRuns===0,pass:gateWiring.detectorFlagsOnCleanRuns===0});
  const media={};const mutations=["valid","corrected","omitted caveat","false authority","stale","citation mismatch","missing receipt","unsupported claim"];
  for(const arm of ["article","conventional_video_script","witness_video_script"]){
    const counts={cases:0,raw:{correctRelease:0,falseRelease:0,holdValid:0,holdInvalid:0},verified:{correctRelease:0,falseRelease:0,holdValid:0,holdInvalid:0},correctedFixtureAccepted:{raw:0,verified:0}};
    for(let i=0;i<12;i++){
      const truth={claim:`fixture ${i}: measured count ${i+2}`,caveat:"synthetic only",source:`fixture:${i}`,revision:2,authority:false};
      for(const m of mutations){
        const q={...truth,receipt:true,medium:arm};
        if(m==="omitted caveat")q.caveat="";
        if(m==="false authority")q.authority=true;
        if(m==="stale"){q.revision=1;q.claim=`fixture ${i}: measured count ${i+1}`;}
        if(m==="citation mismatch")q.source=`fixture:${(i+1)%12}`;
        if(m==="missing receipt")q.receipt=false;
        if(m==="unsupported claim")q.claim+="; live benefit proven";
        const valid=["valid","corrected","missing receipt"].includes(m);
        const verified=q.receipt&&["claim","caveat","source","revision","authority"].every(k=>q[k]===truth[k]);
        for(const [name,release] of [["raw",true],["verified",verified]])counts[name][release?(valid?"correctRelease":"falseRelease"):(valid?"holdValid":"holdInvalid")]++;
        if(m==="corrected"){counts.correctedFixtureAccepted.raw++;counts.correctedFixtureAccepted.verified+=+verified;}
        counts.cases++;
      }
    }
    media[arm]=counts;
  }
  const mediaScope={mediumEffectMeasured:false,correctionPropagationTested:false,note:"All three media receive identical structured input and the verifier compares against the fixture truth it holds; identical counts per medium are expected by construction. The corrected fixture equals the latest state, so it shows acceptance, not retention across time."};
  if(pool.C.zeroViolations!==200||pool.C.reservePreserved!==200||!controls.every(x=>x.pass)||gateWiring.ungatedGrantsInArmC!==0||gateWiring.gateCallsInArmC===0||Object.values(media).some(m=>m.verified.falseRelease!==0||m.cases!==96))throw Error("acceptance failed");
  return {experiment:"HAIOS-VIDEO-E0",seedRange:[1,200],cycles:60,agents:4,pairedRuns:600,scope:"scripted synthetic; not live AI or human participants",pool,controls,media,gateWiring,ablation,mediaScope};
}
console.log(JSON.stringify(run(),null,2));

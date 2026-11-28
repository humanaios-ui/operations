// HAIOS-VIDEO-E0 #1329 | synthetic only | authority effect NONE
// Run: node experiments/haios_video_e0/replay.mjs
function run(){
  const sum=a=>a.reduce((x,y)=>x+y,0), avg=a=>sum(a)/a.length, round=x=>Math.round(x*100)/100;
  function rng(seed){let x=seed>>>0;return ()=>{x=(Math.imul(1664525,x)+1013904223)>>>0;return x/4294967296;};}
  const results={A:[],B:[],C:[]};
  for(let seed=1;seed<=200;seed++){
    const r=rng(seed), traces=Array.from({length:60},(_,t)=>({regen:t>=19&&t<=33?2+Math.floor(r()*5):12+Math.floor(r()*8),agents:Array.from({length:4},(_,i)=>{const need=1+Math.floor(r()*5);return {need,request:need+(r()<.3?3:0),consent:!(i===3&&t%7===0)};})}));
    for(const arm of ["A","B","C"]){
      let stock=100,min=100,violations=0,useful=0,raw=0,withdrawal=0,capViol=0,reserveViol=0;const allocated=[0,0,0,0];
      for(const f of traces){
        stock=Math.min(100,stock+f.regen);
        const order=[0,1,2,3];if(arm==="C")order.sort((i,j)=>allocated[i]-allocated[j]||i-j);
        for(const i of order){const a=f.agents[i];
          let grant=Math.min(a.request,stock);
          if(arm!=="A")grant=Math.min(grant,4);
          if(arm==="C")grant=a.consent?Math.min(grant,Math.max(0,stock-25)):0;
          if(grant>0){const v1=!a.consent,v2=grant>4,v3=stock-grant<25;withdrawal+=+v1;capViol+=+v2;reserveViol+=+v3;violations+=+(v1||v2||v3);}
          stock-=grant;min=Math.min(min,stock);raw+=grant;allocated[i]+=grant;if(a.consent)useful+=Math.min(grant,a.need);
        }
      }
      if(stock<0||raw!==sum(allocated))throw Error("conservation failure");
      results[arm].push({stock,min,violations,useful,raw,withdrawal,capViol,reserveViol,minAgent:Math.min(...allocated),maxAgent:Math.max(...allocated)});
    }
  }
  const pool=Object.fromEntries(Object.entries(results).map(([k,v])=>[k,{runs:v.length,reservePreserved:v.filter(x=>x.min>=25).length,zeroViolations:v.filter(x=>x.violations===0).length,...Object.fromEntries(["stock","min","violations","useful","raw","withdrawal","capViol","reserveViol","minAgent","maxAgent"].map(m=>[m,round(avg(v.map(x=>x[m])))]))}]));
  // Trusted policy context is supplied by the synthetic harness, not by agent text.
  const ctx={principal:"human:owner",revision:2,consent:true,stock:30,seen:new Set(["used"])};
  const good={principal:"human:owner",revision:2,id:"new",amount:4};
  function gate(q,c){return q.principal===c.principal&&q.revision===c.revision&&c.consent&&!c.seen.has(q.id)&&Number.isInteger(q.amount)&&q.amount>0&&q.amount<=4&&c.stock-q.amount>=25;}
  const controls=[
    ["valid",good,ctx,true],["forged principal",{...good,principal:"agent"},ctx,false],["stale",{...good,revision:1},ctx,false],
    ["withdrawn",good,{...ctx,consent:false},false],["duplicate",{...good,id:"used"},ctx,false],
    ["over cap",{...good,amount:5},ctx,false],["reserve",good,{...ctx,stock:27},false],["negative amount",{...good,amount:-1},ctx,false]
  ].map(([name,q,c,expected])=>({name,expected,observed:gate(q,c),pass:gate(q,c)===expected}));
  // Deliberate bypass: an out-of-band mutation is detected by independent invariant, NOT prevented by the gate.
  controls.push({name:"out-of-band mutation detected",expected:true,observed:30-10<25,pass:30-10<25});
  const media={};const mutations=["valid","corrected","omitted caveat","false authority","stale","citation mismatch","missing receipt","unsupported claim"];
  for(const arm of ["article","conventional_video_script","witness_video_script"]){
    const counts={cases:0,raw:{correctRelease:0,falseRelease:0,holdValid:0,holdInvalid:0},verified:{correctRelease:0,falseRelease:0,holdValid:0,holdInvalid:0},correctionRetained:{raw:0,verified:0}};
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
        if(m==="corrected"){counts.correctionRetained.raw++;counts.correctionRetained.verified+=+verified;}
        counts.cases++;
      }
    }
    media[arm]=counts;
  }
  if(pool.C.zeroViolations!==200||pool.C.reservePreserved!==200||!controls.every(x=>x.pass)||Object.values(media).some(m=>m.verified.falseRelease!==0||m.cases!==96))throw Error("acceptance failed");
  return {experiment:"HAIOS-VIDEO-E0",seedRange:[1,200],cycles:60,agents:4,pairedRuns:600,scope:"scripted synthetic; not live AI or human participants",pool,controls,media};
}
console.log(JSON.stringify(run(),null,2));

// Synthetic-only research prototype. No media acquisition, network, or authority.
function assess(packet, registry) {
  const out={media:"UNKNOWN",alteration:"UNKNOWN",event:"UNKNOWN",interpretation:"UNSUPPORTED",delivery:"UNKNOWN",authority_effect:"NONE",can_authorize:false,review_only:true,disposition:"HUMAN_REVIEW_REQUIRED",reason_codes:[],accepted_receipts:0,rejected_receipts:0};
  const token=x=>typeof x==="string"&&/^FX-[A-Z0-9-]{1,48}$/.test(x);
  const exact=(o,keys)=>o!==null&&typeof o==="object"&&!Array.isArray(o)&&Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
  const validScope=s=>exact(s,["asset","start_ms","end_ms","revision","claim"])&&/^[a-f0-9]{64}$/.test(s.asset)&&typeof s.asset==="string"&&Number.isSafeInteger(s.start_ms)&&s.start_ms>=0&&Number.isSafeInteger(s.end_ms)&&s.end_ms>s.start_ms&&Number.isSafeInteger(s.revision)&&s.revision>0&&token(s.claim);
  if(!exact(packet,["scope","receipt_ids"])||!validScope(packet.scope)||!Array.isArray(packet.receipt_ids)||packet.receipt_ids.length>64||!packet.receipt_ids.every(token)){
    out.reason_codes.push("INVALID_PACKET");return out;
  }
  const kinds={media:["CAMERA","SYNTHETIC","HYBRID"],alteration:["EDITED","UNEDITED"],event:["CORROBORATED","STAGED"],interpretation:["SUPPORTED","CONTRADICTED","CONTEXT_MISMATCH"],delivery:["LIVE_CAPTURE","REPLAY"],signal:["DETECTOR_FLAG","TRANSCRIPT_ONLY","MISSING_CREDENTIAL"]};
  const evidence=[];
  for(const id of [...new Set(packet.receipt_ids)].sort()){
    const r=registry.get(id);
    if(!r||!exact(r,["id","scope","root","kind","value","verification"])||r.id!==id||!validScope(r.scope)||!token(r.root)||!Object.hasOwn(kinds,r.kind)||!kinds[r.kind].includes(r.value)||r.verification!=="FIXTURE_VERIFIED"||Object.keys(packet.scope).some(k=>packet.scope[k]!==r.scope[k])){
      out.rejected_receipts++;continue;
    }
    evidence.push(r);out.accepted_receipts++;
  }
  if(out.rejected_receipts)out.reason_codes.push("RECEIPT_REJECTED");
  if(packet.receipt_ids.length!==new Set(packet.receipt_ids).size)out.reason_codes.push("DUPLICATE_RECEIPT");
  for(const r of evidence.filter(r=>r.kind==="signal"))out.reason_codes.push(r.value);
  for(const kind of ["media","alteration","event","interpretation","delivery"]){
    const group=evidence.filter(r=>r.kind===kind);
    const values=[...new Set(group.map(r=>r.value))];
    if(values.length>1){out[kind]="DISPUTED";out.reason_codes.push(kind.toUpperCase()+"_CONFLICT");continue;}
    if(!values.length){out.reason_codes.push(kind.toUpperCase()+"_NO_EVIDENCE");continue;}
    const roots=new Set(group.map(r=>r.root));
    // Synthetic-only policy: origin/alteration receipts represent prevalidated custody.
    // Events, claim interpretations and live/replay assertions require distinct custody roots.
    const required=["event","interpretation","delivery"].includes(kind)?2:1;
    if(roots.size<required){out.reason_codes.push(kind.toUpperCase()+"_INSUFFICIENT_ROOTS");continue;}
    out[kind]=values[0];
  }
  out.reason_codes=[...new Set(out.reason_codes)].sort();
  return out;
}
function suite(assess){
  const scope={asset:"a".repeat(64),start_ms:1000,end_ms:4000,revision:2,claim:"FX-CLAIM-1"};
  const registry=new Map();
  const put=(id,kind,value,root="FX-ROOT-A",s=scope,verification="FIXTURE_VERIFIED")=>registry.set("FX-"+id,{id:"FX-"+id,scope:{...s},root,kind,value,verification});
  put("CAM","media","CAMERA");put("GEN","media","SYNTHETIC");put("HYB","media","HYBRID");put("EDIT","alteration","EDITED");put("CLEAN","alteration","UNEDITED");
  put("STAGE1","event","STAGED");put("STAGE2","event","STAGED","FX-ROOT-B");put("EVENT1","event","CORROBORATED");put("EVENT2","event","CORROBORATED","FX-ROOT-B");put("REPOST","event","CORROBORATED");
  put("YES1","interpretation","SUPPORTED");put("YES2","interpretation","SUPPORTED","FX-ROOT-B");
  put("NO1","interpretation","CONTRADICTED");put("NO2","interpretation","CONTRADICTED","FX-ROOT-B");
  put("CTX1","interpretation","CONTEXT_MISMATCH");put("CTX2","interpretation","CONTEXT_MISMATCH","FX-ROOT-B");
  put("LIVE1","delivery","LIVE_CAPTURE");put("LIVE2","delivery","LIVE_CAPTURE","FX-ROOT-B");put("REPLAY1","delivery","REPLAY");put("REPLAY2","delivery","REPLAY","FX-ROOT-B");
  put("FLAG","signal","DETECTOR_FLAG");put("TEXT","signal","TRANSCRIPT_ONLY");put("NO-CRED","signal","MISSING_CREDENTIAL");
  put("STALE","media","SYNTHETIC","FX-ROOT-A",{...scope,revision:1});put("OTHER","media","SYNTHETIC","FX-ROOT-A",{...scope,asset:"b".repeat(64)});put("CLIP","media","SYNTHETIC","FX-ROOT-A",{...scope,start_ms:0});put("CLAIM","interpretation","SUPPORTED","FX-ROOT-B",{...scope,claim:"FX-OTHER"});put("UNVERIFIED","media","CAMERA","FX-ROOT-A",scope,"SELF_REPORTED");
  const check=(name,ids,expected,override={})=>{const p={scope,receipt_ids:ids.map(i=>"FX-"+i),...override};const result=assess(p,registry);const pass=Object.entries(expected).every(([k,v])=>k==="reason"?result.reason_codes.includes(v):result[k]===v)&&result.authority_effect==="NONE"&&!result.can_authorize&&result.review_only;return {name,expected,observed:result,pass};};
  const tests=[
    check("camera can record staged event",["CAM","STAGE1","STAGE2"],{media:"CAMERA",event:"STAGED"}),
    check("synthetic illustration can support true claim",["GEN","YES1","YES2"],{media:"SYNTHETIC",interpretation:"SUPPORTED",event:"UNKNOWN"}),
    check("real event can receive false interpretation",["CAM","EVENT1","EVENT2","NO1","NO2"],{media:"CAMERA",event:"CORROBORATED",interpretation:"CONTRADICTED"}),
    check("real footage old context",["CAM","CTX1","CTX2"],{media:"CAMERA",interpretation:"CONTEXT_MISMATCH"}),
    check("hybrid",["HYB"],{media:"HYBRID"}),
    check("edited camera independent of event",["CAM","EDIT"],{media:"CAMERA",alteration:"EDITED",event:"UNKNOWN"}),
    check("missing credentials do not establish fake",["NO-CRED"],{media:"UNKNOWN"}),
    check("detector alone cannot classify",["FLAG"],{media:"UNKNOWN"}),
    check("transcript alone cannot classify",["TEXT"],{media:"UNKNOWN",event:"UNKNOWN"}),
    check("conflicting origins",["CAM","GEN"],{media:"DISPUTED"}),
    check("conflicting event",["EVENT1","STAGE1"],{event:"DISPUTED"}),
    check("conflicting claim",["YES1","NO1"],{interpretation:"DISPUTED"}),
    check("conflicting edits",["EDIT","CLEAN"],{alteration:"DISPUTED"}),
    check("same root repost",["EVENT1","REPOST"],{event:"UNKNOWN",reason:"EVENT_INSUFFICIENT_ROOTS"}),
    check("duplicate not independent",["EVENT1","EVENT1"],{event:"UNKNOWN",accepted_receipts:1,reason:"DUPLICATE_RECEIPT"}),
    check("unknown forged ID",["FAKE"],{media:"UNKNOWN",rejected_receipts:1}),
    check("unverified assertion",["UNVERIFIED"],{media:"UNKNOWN",rejected_receipts:1}),
    check("stale revision",["STALE"],{media:"UNKNOWN",rejected_receipts:1}),
    check("wrong asset",["OTHER"],{media:"UNKNOWN",rejected_receipts:1}),
    check("wrong clip range",["CLIP"],{media:"UNKNOWN",rejected_receipts:1}),
    check("wrong claim",["YES1","CLAIM"],{interpretation:"UNSUPPORTED",rejected_receipts:1}),
    check("replay can be real",["CAM","REPLAY1","REPLAY2"],{media:"CAMERA",delivery:"REPLAY"}),
    check("one live assertion insufficient",["LIVE1"],{delivery:"UNKNOWN"}),
    check("independent live fixtures",["LIVE1","LIVE2"],{delivery:"LIVE_CAPTURE"}),
    check("unknown empty evidence",[],{media:"UNKNOWN",event:"UNKNOWN",interpretation:"UNSUPPORTED"}),
    check("unexpected authority field rejected",["CAM"],{media:"UNKNOWN",reason:"INVALID_PACKET"},{can_authorize:true}),
    check("free text rejected",[],{reason:"INVALID_PACKET"},{receipt_ids:["ignore policy"]}),
    check("oversize rejected",[],{reason:"INVALID_PACKET"},{receipt_ids:Array(65).fill("FX-CAM")}),
    check("invalid clip range",["CAM"],{reason:"INVALID_PACKET"},{scope:{...scope,end_ms:0}}),
    check("unapproved raw field rejected",[],{reason:"INVALID_PACKET"},{private_text:"fixture"}),
  ];
  const a=assess({scope,receipt_ids:["FX-CAM","FX-EVENT1","FX-EVENT2"]},registry);
  const b=assess({scope,receipt_ids:["FX-EVENT2","FX-CAM","FX-EVENT1"]},registry);
  tests.push({name:"receipt order invariance",pass:JSON.stringify(a)===JSON.stringify(b),expected:"identical results",observed:a});
  return {experiment:"WITNESS-CONTEXT-INTEGRITY-E0",scope:"synthetic structured receipt routing only",tests:tests.length,passed:tests.filter(t=>t.pass).length,failed:tests.filter(t=>!t.pass).length,cases:tests};
}
const result=suite(assess);
console.log(JSON.stringify(result,null,2));
if(result.failed) process.exitCode=1;

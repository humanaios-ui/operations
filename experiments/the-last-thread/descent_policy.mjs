/** Descent v3.0 design specimen. PURE reference functions; NOT imported into the live game.
 * Rule authority always remains with the existing campaign server/reducer.
 */
export const DESIGN_VERSION = "descent.v3.0-candidate";
const STAGES = Object.freeze([
  {at:12,id:"LATTICE_FAILURE"},{at:20,id:"FURNACE_IRREVERSIBLE"},
  {at:25,id:"TETHER_COLLAPSE_IF_UNSECURED"},{at:27,id:"SHIELD_FIRST_CONTACT"},
  {at:30,id:"NULL_CENTER_CROSSING"}
]);
const ALLOWED_INTENTS = Object.freeze({
  "TOK-AI-001": Object.freeze({
    offer: ["risk_fragment"],threaten:["pressure_warning"],
    illusion:["visual_echo"],propose_modifier:["null_silence"],
    propose_route_reveal:["rumor_route"],request_spawn:["turned_echo"]
  }),
  "TOK-AI-002": Object.freeze({
    offer:["faction_favor"],demand:["supply_trade"],withdraw:["revoke_offer"]
  }),
  "TOK-AI-003": Object.freeze({
    pact:["shielded_transfer","quiet_descent","forgo_fragments"]
  }),
  "TOK-AI-004": Object.freeze({
    ping:["glyph_ping"],warn:["glyph_warning"],
    offer_passage:["pod_passage"],withdraw:["pod_withdraw"]
  })
});
const ALL_STATES = Object.freeze({
  "risk_fragment":{cost:"influence",approval:true},
  "pressure_warning":{cost:"influence",approval:false},
  "visual_echo":{cost:"influence",approval:false},
  "null_silence":{cost:"influence",approval:true},
  "rumor_route":{cost:"influence",approval:true},
  "turned_echo":{cost:"influence",approval:false},
  "faction_favor":{cost:"favor",approval:true},
  "supply_trade":{cost:"favor",approval:true},
  "revoke_offer":{cost:"favor",approval:false},
  "shielded_transfer":{cost:"favor",approval:true},
  "quiet_descent":{cost:"favor",approval:true},
  "forgo_fragments":{cost:"favor",approval:true},
  "glyph_ping":{cost:"pod_favor",approval:false},
  "glyph_warning":{cost:"pod_favor",approval:false},
  "pod_passage":{cost:"pod_favor",approval:true},
  "pod_withdraw":{cost:"pod_favor",approval:false}
});
function integer(x,min,max){return Number.isInteger(x)&&x>=min&&x<=max;}
export function campaignDelta(runTick){
  if(!integer(runTick,0,30))throw Error("bad run_tick");
  return Math.min(6,1+Math.ceil(runTick/6));
}
export function settleCampaign(campaign,run){
  if(!campaign||!integer(campaign.world_tick,0,30)||!Array.isArray(campaign.settled_ids))throw Error("bad campaign");
  if(!run||typeof run.contract_id!=="string"||!/^[a-zA-Z0-9_-]{1,80}$/.test(run.contract_id)||
     !integer(run.run_tick,0,30)||typeof run.extracted!=="boolean")throw Error("bad run");
  if(campaign.settled_ids.includes(run.contract_id))return {status:"DUPLICATE_IGNORED",campaign:structuredClone(campaign),delta:0,events:[]};
  if(campaign.world_tick>=30)throw Error("campaign finished");
  const next=structuredClone(campaign);
  const previous=next.world_tick;
  next.world_tick=Math.min(30,previous+campaignDelta(run.run_tick));
  next.settled_ids.push(run.contract_id);
  if(next.settled_ids.length>60)throw Error("settlement ledger too large");
  const events=STAGES.filter(e=>previous<e.at&&e.at<=next.world_tick).map(e=>e.id);
  return {status:run.extracted?"SETTLED_EXTRACTED":"SETTLED_UNEXTRACTED",
    delta:next.world_tick-previous,events,campaign:next};
}
export function validateAgentIntent(intent,context){
  const reject=reason=>({accepted:false,reason,fallback:"NO_CHANGE"});
  if(!intent||typeof intent!=="object"||Array.isArray(intent)||!context||typeof context!=="object")return reject("MALFORMED");
  const keys=Object.keys(intent).sort();
  const schema=["action_id","actor_id","contract_id","effect_id","ruleset_version","target_id"].sort();
  if(keys.length!==schema.length||keys.some((x,i)=>x!==schema[i]))return reject("UNEXPECTED_KEYS");
  if(intent.ruleset_version!==DESIGN_VERSION)return reject("WRONG_RULESET");
  if(intent.contract_id!==context.contract_id||!context.contract_id)return reject("CONTRACT_SCOPE");
  const acts=ALLOWED_INTENTS[intent.actor_id];
  if(!acts||!Object.prototype.hasOwnProperty.call(acts,intent.action_id))return reject("ACTOR_ACTION_SCOPE");
  if(!acts[intent.action_id].includes(intent.effect_id))return reject("EFFECT_OUT_OF_SCOPE");
  if(typeof intent.target_id!=="string"||!Array.isArray(context.allowed_targets)||
      !context.allowed_targets.includes(intent.target_id))return reject("TARGET_SCOPE");
  if(!integer(context.run_tick,0,30)||context.run_tick>=30||
    context.active!==true)return reject("RUN_NOT_ACTIVE");
  const effect=ALL_STATES[intent.effect_id];
  const resource=context.resources?.[effect.cost];
  if(!integer(resource,0,100)||resource<1)return reject("INSUFFICIENT_AGENT_RESOURCE");
  if(effect.approval===true && context.player_approved!==true)
    return {accepted:false,reason:"PLAYER_CONFIRMATION_REQUIRED",fallback:"SHOW_OFFER_ONLY"};
  return {accepted:true,reason:"VALID_TYPED_INTENT",effect_id:intent.effect_id,authority:"CANDIDATE_ONLY"};
}
export function agentFallback(actorId){
  return actorId==="TOK-AI-004"?{intent:"ping",effect_id:"glyph_ping",presentation:"glyph_warning"}
    :{intent:"pass",effect_id:null,presentation:"NPC action unavailable"};
}
export const DESIGN_POLICY = Object.freeze({
  ruleset:DESIGN_VERSION,
  event_stages:STAGES,
  agent_actions:ALLOWED_INTENTS,
  note:"This module does not write game state or invoke a language model."
});

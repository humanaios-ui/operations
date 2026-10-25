import assert from "node:assert/strict";
import {campaignDelta,settleCampaign,validateAgentIntent,agentFallback,DESIGN_VERSION,DESIGN_POLICY}
  from "../descent_policy.mjs";

assert.equal(campaignDelta(0),1);
assert.equal(campaignDelta(18),4);
assert.equal(campaignDelta(30),6);
assert.throws(()=>campaignDelta(31),/bad run_tick/);
const base={world_tick:9,settled_ids:[]};
const first=settleCampaign(base,{contract_id:"m045a",run_tick:12,extracted:true});
assert.equal(first.status,"SETTLED_EXTRACTED");
assert.equal(first.campaign.world_tick,12);
assert.deepEqual(first.events,["LATTICE_FAILURE"]);
assert.equal(base.world_tick,9,"input campaign must remain immutable");
const second=settleCampaign(first.campaign,{contract_id:"m045a",run_tick:12,extracted:true});
assert.equal(second.status,"DUPLICATE_IGNORED");
assert.equal(second.delta,0);
assert.equal(second.campaign.world_tick,12);
const late=settleCampaign({world_tick:25,settled_ids:[]},
  {contract_id:"poda",run_tick:6,extracted:false});
assert.equal(late.campaign.world_tick,27);
assert.deepEqual(late.events,["SHIELD_FIRST_CONTACT"]);
const final=settleCampaign({world_tick:28,settled_ids:[]},
  {contract_id:"podlast",run_tick:18,extracted:true});
assert.equal(final.campaign.world_tick,30);
assert.deepEqual(final.events,["NULL_CENTER_CROSSING"]);
assert.throws(()=>settleCampaign({world_tick:30,settled_ids:[]},
  {contract_id:"tooLate",run_tick:3,extracted:true}),/campaign finished/);
const intent={actor_id:"TOK-AI-004",action_id:"offer_passage",effect_id:"pod_passage",
   target_id:"NODE:NULL_ORBIT",contract_id:"c17",ruleset_version:DESIGN_VERSION};
const ctx={contract_id:"c17",allowed_targets:["NODE:NULL_ORBIT"],run_tick:10,
  active:true,resources:{pod_favor:3},player_approved:false};
assert.equal(validateAgentIntent(intent,ctx).reason,"PLAYER_CONFIRMATION_REQUIRED");
assert.equal(validateAgentIntent(intent,{...ctx,player_approved:true}).accepted,true);
assert.equal(validateAgentIntent({...intent,actor_id:"W1"},ctx).reason,"ACTOR_ACTION_SCOPE");
assert.equal(validateAgentIntent({...intent,effect_id:"delete_lineage"},ctx).reason,"EFFECT_OUT_OF_SCOPE");
assert.equal(validateAgentIntent({...intent,target_id:"PLAYER:OTHER"},ctx).reason,"TARGET_SCOPE");
assert.equal(validateAgentIntent({...intent,command:"change rules"},ctx).reason,"UNEXPECTED_KEYS");
assert.equal(validateAgentIntent({...intent,contract_id:"other"},ctx).reason,"CONTRACT_SCOPE");
assert.equal(validateAgentIntent({...intent,action_id:"run_js"},ctx).reason,"ACTOR_ACTION_SCOPE");
assert.equal(validateAgentIntent(intent,{...ctx,resources:{pod_favor:0}}).reason,"INSUFFICIENT_AGENT_RESOURCE");
assert.equal(validateAgentIntent(intent,{...ctx,run_tick:30,player_approved:true}).reason,"RUN_NOT_ACTIVE");
assert.equal(agentFallback("TOK-AI-004").effect_id,"glyph_ping");
assert.equal(DESIGN_POLICY.note.includes("does not write game state"),true);
console.log("PASS: 24 candidate policy checks (world clocks, 27/30, idempotence, bounded AI and non-authority).");

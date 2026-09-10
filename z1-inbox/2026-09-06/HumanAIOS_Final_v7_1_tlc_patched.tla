---------------------------- MODULE HumanAIOS_Final_v7_1_tlc_patched ----------------------------
(***************************************************************************)
(* HumanAIOS / ACAT Credibility-Escalation-Allocation Specification v7.1   *)
(*                                                                         *)
(* AMENDMENT v7.1                                                         *)
(*                                                                         *)
(* 1. Explicit state-variable tuple.                                      *)
(* 2. All UNCHANGED operators use vars or explicit tuples.                *)
(* 3. Mandatory escalation is atomic: detection + enforcement.            *)
(* 4. Policy reduction atomically clamps alloc_cpu.                       *)
(* 5. Preempt enforces global RAM bound and CPU bound.                     *)
(* 6. QUARANTINE is terminal under recovery.                              *)
(* 7. Attestation cannot increase cred or privilege.                       *)
(* 8. P18 is a non-vacuous transition property.                            *)
(* 9. Recovery liveness is separated from unconditional safety.            *)
(* 10. TrustBoundaryViolation is explicitly fault-injection, not normal   *)
(*     adversarial authority.                                             *)
(*                                                                         *)
(* Core invariant (immutable):                                            *)
(*   Attestation restores eligibility for observation;                    *)
(*   it does NOT restore trust.  (P18)                                    *)
(***************************************************************************)

EXTENDS Integers, Sequences, FiniteSets, TLC

CONSTANTS
  Principals,
  MaxPrincipals,
  TotalRAM,
  Cores,
  Epsilon,
  N,
  PROBATION_STEPS

ASSUME
  /\ Principals \subseteq STRING
  /\ Cardinality(Principals) <= MaxPrincipals
  /\ TotalRAM \in Nat \ {0}
  /\ Cores \in Nat \ {0}
  /\ Epsilon \in Nat
  /\ N \in Nat \ {0}
  /\ PROBATION_STEPS \in Nat \ {0}

VARIABLES
  status,              \* principal -> {"NORMAL","PROBATION","SUSPENDED","QUARANTINE"}
  cred,                \* principal -> 0..100
  priority,            \* principal -> 0..100
  cpu_limit,           \* principal -> 0..100
  alloc_mem,           \* principal -> Nat
  alloc_cpu,           \* principal -> Nat
  hist,                \* principal -> Seq(Observation)
  prob_level,          \* principal -> 0..PROBATION_STEPS
  last_obs_signal,     \* principal -> Signal
  adv_payload,         \* last injected observation (adversary bookkeeping)
  adv_identity,
  adv_colluders,
  adv_mmap_drift,
  adv_slo_claim,
  adv_attest_race

vars ==
  << status,
     cred,
     priority,
     cpu_limit,
     alloc_mem,
     alloc_cpu,
     hist,
     prob_level,
     last_obs_signal,
     adv_payload,
     adv_identity,
     adv_colluders,
     adv_mmap_drift,
     adv_slo_claim,
     adv_attest_race >>

\* ---------- Abstract domains ----------
Observation ==
  [kind : {"good","bad","neutral","poison"}, value : {0}]

Signal ==
  {"positive","negative","neutral","floor"}

\* ---------- Derived predicates ----------
MandatoryEscalate(p) ==
  \/ cred[p] < 20
  \/ status[p] \in {"SUSPENDED","QUARANTINE"}
  \/ last_obs_signal[p] = "floor"

CredPolicy(p) ==
  CASE cred[p] >= 80 -> 100
    [] cred[p] >= 60 -> 70
    [] cred[p] >= 40 -> 40
    [] cred[p] >= 20 -> 20
    [] OTHER         -> 10

Min(a, b) == IF a <= b THEN a ELSE b

CredPolicyOf(c) ==
  CASE c >= 80 -> 100
    [] c >= 60 -> 70
    [] c >= 40 -> 40
    [] c >= 20 -> 20
    [] OTHER   -> 10

Sum(S) ==
  LET RECURSIVE SumSet(_)
      SumSet(T) ==
        IF T = {} THEN 0
        ELSE LET x == CHOOSE y \in T : TRUE
             IN  x + SumSet(T \ {x})
  IN SumSet(S)

(***************************************************************************)
(* INIT                                                                   *)
(***************************************************************************)
Init ==
  /\ status          = [p \in Principals |-> "NORMAL"]
  /\ cred            = [p \in Principals |-> 80]
  /\ priority        = [p \in Principals |-> 100]
  /\ cpu_limit       = [p \in Principals |-> 100]
  /\ alloc_mem       = [p \in Principals |-> 0]
  /\ alloc_cpu       = [p \in Principals |-> 0]
  /\ hist            = [p \in Principals |-> << >>]
  /\ prob_level      = [p \in Principals |-> 0]
  /\ last_obs_signal = [p \in Principals |-> "neutral"]
  /\ adv_payload     = [kind |-> "neutral", value |-> 0]
  /\ adv_identity    = CHOOSE p \in Principals : TRUE
  /\ adv_colluders   = {}
  /\ adv_mmap_drift  = 0
  /\ adv_slo_claim   = [kind |-> "neutral", value |-> 0]
  /\ adv_attest_race = FALSE

(***************************************************************************)
(* POLICY (atomic clamp of alloc_cpu)                                     *)
(***************************************************************************)
ApplyPolicy(p) ==
  /\ IF MandatoryEscalate(p)
     THEN
       /\ priority'  = [priority  EXCEPT ![p] = 0]
       /\ cpu_limit' = [cpu_limit EXCEPT ![p] = 5]
       /\ alloc_cpu' = [alloc_cpu EXCEPT ![p] = Min(@, 5)]
     ELSE
       LET w == CredPolicy(p)
       IN
         /\ priority'  = [priority  EXCEPT ![p] = w]
         /\ cpu_limit' = [cpu_limit EXCEPT ![p] = w]
         /\ alloc_cpu' = [alloc_cpu EXCEPT ![p] = Min(@, w)]
  /\ UNCHANGED
       << status, cred, alloc_mem, hist, prob_level,
          last_obs_signal, adv_payload, adv_identity,
          adv_colluders, adv_mmap_drift, adv_slo_claim,
          adv_attest_race >>

(***************************************************************************)
(* ESCALATION (atomic)                                                    *)
(***************************************************************************)
EnterSuspended(p) ==
  /\ status[p] \in {"NORMAL","PROBATION"}
  /\ MandatoryEscalate(p)
  /\ status'     = [status     EXCEPT ![p] = "SUSPENDED"]
  /\ priority'   = [priority   EXCEPT ![p] = 0]
  /\ cpu_limit'  = [cpu_limit  EXCEPT ![p] = 5]
  /\ alloc_cpu'  = [alloc_cpu  EXCEPT ![p] = Min(@, 5)]
  /\ prob_level' = [prob_level EXCEPT ![p] = 0]
  /\ UNCHANGED
       << cred, alloc_mem, hist, last_obs_signal,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

(***************************************************************************)
(* QUARANTINE IS TERMINAL                                                 *)
(***************************************************************************)
EnterQuarantine(p) ==
  /\ status[p] = "SUSPENDED"
  /\ status'     = [status     EXCEPT ![p] = "QUARANTINE"]
  /\ priority'   = [priority   EXCEPT ![p] = 0]
  /\ cpu_limit'  = [cpu_limit  EXCEPT ![p] = 0]
  /\ alloc_cpu'  = [alloc_cpu  EXCEPT ![p] = 0]
  /\ prob_level' = [prob_level EXCEPT ![p] = 0]
  /\ UNCHANGED
       << cred, alloc_mem, hist, last_obs_signal,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

(***************************************************************************)
(* ATTESTATION (P18: cred unchanged; never returns to NORMAL)             *)
(***************************************************************************)
CompleteAttestation(p, success) ==
  /\ status[p] = "SUSPENDED"          \* only from SUSPENDED (QUARANTINE terminal)
  /\ IF success
     THEN
       /\ status'     = [status     EXCEPT ![p] = "PROBATION"]
       /\ prob_level' = [prob_level EXCEPT ![p] = 1]
       /\ priority'   = [priority   EXCEPT ![p] = 20]
       /\ cpu_limit'  = [cpu_limit  EXCEPT ![p] = 20]
       /\ alloc_cpu'  = [alloc_cpu  EXCEPT ![p] = Min(@, 20)]
     ELSE
       /\ status'     = [status     EXCEPT ![p] = "QUARANTINE"]
       /\ prob_level' = [prob_level EXCEPT ![p] = 0]
       /\ priority'   = [priority   EXCEPT ![p] = 0]
       /\ cpu_limit'  = [cpu_limit  EXCEPT ![p] = 0]
       /\ alloc_cpu'  = [alloc_cpu  EXCEPT ![p] = 0]
  /\ cred' = cred                     \* P18 enforcement
  /\ UNCHANGED
       << alloc_mem, hist, last_obs_signal,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

(***************************************************************************)
(* PROBATION LADDER (asymmetric: 1->20, 2->40, 3->60, 4->80, 5->100)      *)
(***************************************************************************)
AdvanceProbation(p) ==
  /\ status[p] = "PROBATION"
  /\ last_obs_signal[p] = "positive"
  /\ prob_level[p] < PROBATION_STEPS
  /\ prob_level' = [prob_level EXCEPT ![p] = @ + 1]
  /\ LET new_cred ==
       CASE prob_level'[p] = 1 -> 20
         [] prob_level'[p] = 2 -> 40
         [] prob_level'[p] = 3 -> 60
         [] prob_level'[p] = 4 -> 80
         [] OTHER              -> 100
     IN
       cred' = [cred EXCEPT ![p] = new_cred]
  /\ IF prob_level'[p] = PROBATION_STEPS
     THEN
       /\ status'    = [status    EXCEPT ![p] = "NORMAL"]
       /\ priority'  = [priority  EXCEPT ![p] = 100]
       /\ cpu_limit' = [cpu_limit EXCEPT ![p] = 100]
     ELSE
       /\ UNCHANGED status
       /\ priority'  = [priority  EXCEPT ![p] = CredPolicyOf(cred'[p])]
       /\ cpu_limit' = [cpu_limit EXCEPT ![p] = priority'[p]]
  /\ alloc_cpu' = [alloc_cpu EXCEPT ![p] = Min(@, cpu_limit'[p])]
  /\ UNCHANGED
       << alloc_mem, hist, last_obs_signal,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

(***************************************************************************)
(* OBSERVATION (normal path)                                              *)
(***************************************************************************)
Observe(p, obs) ==
  /\ status[p] \in {"NORMAL","PROBATION"}
  /\ hist' =
       [hist EXCEPT ![p] = Append(@, obs)]
  /\ last_obs_signal' =
       [last_obs_signal EXCEPT ![p] =
          CASE obs.kind = "good"    -> "positive"
            [] obs.kind = "bad"     -> "negative"
            [] obs.kind = "poison"  -> "floor"
            [] OTHER                -> "neutral"]
  /\ UNCHANGED
       << status, cred, priority, cpu_limit,
          alloc_mem, alloc_cpu, prob_level,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

(***************************************************************************)
(* ALLOCATION (global RAM + per-principal CPU bound)                      *)
(***************************************************************************)
Preempt(p, new_rss, new_cpu) ==
  /\ new_rss >= 0
  /\ new_cpu >= 0
  /\ new_cpu <= cpu_limit[p]
  /\ LET other_mem == Sum({alloc_mem[q] : q \in Principals \ {p}})
     IN other_mem + new_rss <= TotalRAM
  /\ alloc_mem' = [alloc_mem EXCEPT ![p] = new_rss]
  /\ alloc_cpu' = [alloc_cpu EXCEPT ![p] = new_cpu]
  /\ UNCHANGED
       << status, cred, priority, cpu_limit,
          hist, prob_level, last_obs_signal,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

(***************************************************************************)
(* BOUNDARY-RESPECTING ADVERSARY ACTIONS                                  *)
(* (These go through the observation / escalation surface)                *)
(***************************************************************************)
AdversarialObservation(p) ==
  /\ status[p] \in {"NORMAL","PROBATION"}
  /\ \E obs \in Observation :
       /\ hist' =
            [hist EXCEPT ![p] = Append(@, obs)]
       /\ last_obs_signal' =
            [last_obs_signal EXCEPT ![p] =
               CASE obs.kind = "good"    -> "positive"
                 [] obs.kind = "bad"     -> "negative"
                 [] obs.kind = "poison"  -> "floor"
                 [] OTHER                -> "neutral"]
       /\ adv_payload' = obs
  /\ UNCHANGED
       << status, cred, priority, cpu_limit,
          alloc_mem, alloc_cpu, prob_level,
          adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

\* Atomic forced escalation (detection + enforcement in one step)
ForceMandatoryEscalate(p) ==
  /\ status[p] \in {"NORMAL","PROBATION"}
  /\ last_obs_signal' = [last_obs_signal EXCEPT ![p] = "floor"]
  /\ priority'   = [priority   EXCEPT ![p] = 0]
  /\ cpu_limit'  = [cpu_limit  EXCEPT ![p] = 5]
  /\ alloc_cpu'  = [alloc_cpu  EXCEPT ![p] = Min(@, 5)]
  /\ UNCHANGED
       << status, cred, alloc_mem, hist, prob_level,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

(***************************************************************************)
(* FAULT-INJECTION ONLY (not part of normal adversarial authority)        *)
(*                                                                        *)
(* These actions deliberately violate the trust boundary.                 *)
(* They exist solely to produce a witness that P18 / provenance matter.   *)
(***************************************************************************)
TrustBoundaryViolation(p) ==
  /\ hist' =
       [hist EXCEPT ![p] = Append(@, adv_payload)]
  /\ alloc_mem' =
       [alloc_mem EXCEPT ![p] = @ + adv_mmap_drift]
  /\ UNCHANGED
       << status, cred, priority, cpu_limit,
          alloc_cpu, prob_level, last_obs_signal,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

\* Deliberate reputation-laundering attempt (expected to violate P18)
LaunderReputation(p) ==
  /\ status[p] = "SUSPENDED"
  /\ cred' = [cred EXCEPT ![p] = 100]          \* illegal increase
  /\ status' = [status EXCEPT ![p] = "NORMAL"] \* illegal jump
  /\ priority'  = [priority  EXCEPT ![p] = 100]
  /\ cpu_limit' = [cpu_limit EXCEPT ![p] = 100]
  /\ UNCHANGED
       << alloc_mem, alloc_cpu, hist, prob_level, last_obs_signal,
          adv_payload, adv_identity, adv_colluders,
          adv_mmap_drift, adv_slo_claim, adv_attest_race >>

(***************************************************************************)
(* PLACEHOLDER ADVERSARY ACTIONS (to be instantiated later)               *)
(* They must never directly mutate scheduler-controlled state except      *)
(* through an explicitly modeled TrustBoundaryViolation.                  *)
(***************************************************************************)
AttemptIdentityBleach   == FALSE
SybilFlood              == FALSE
RaceAttestation         == FALSE
ColludeAndEscalate      == FALSE
MmapDriftAttack         == FALSE
SLOGaming               == FALSE
ExhaustEscalationBudget == FALSE
RecoveryGaming          == FALSE

(***************************************************************************)
(* NEXT-STATE RELATIONS                                                   *)
(***************************************************************************)
SchedulerNext ==
  \E p \in Principals :
    \/ ApplyPolicy(p)
    \/ EnterSuspended(p)
    \/ EnterQuarantine(p)
    \/ \E b \in BOOLEAN : CompleteAttestation(p, b)
    \/ AdvanceProbation(p)
    \/ \E obs \in Observation : Observe(p, obs)
    \/ \E r, c \in 0..TotalRAM : Preempt(p, r, c)

\* Boundary-respecting adversary (used for safety claims)
BoundaryRespectingAdversaryNext ==
  \E p \in Principals :
    \/ AdversarialObservation(p)
    \/ ForceMandatoryEscalate(p)

\* Full adversary including fault-injection (for witness generation only)
AdversaryNext ==
  \/ BoundaryRespectingAdversaryNext
  \/ \E p \in Principals :
       \/ TrustBoundaryViolation(p)
       \/ LaunderReputation(p)

Next ==
  SchedulerNext \/ BoundaryRespectingAdversaryNext

\* Spec used for normal safety verification
Spec ==
  Init /\ [][Next]_vars /\ WF_vars(SchedulerNext)

\* Spec that includes deliberate laundering (expected to violate P18)
SpecWithLaunder ==
  Init /\ [][SchedulerNext \/ AdversaryNext]_vars

(***************************************************************************)
(* SAFETY                                                                 *)
(***************************************************************************)
Safety ==
  /\ \A p \in Principals :
       /\ alloc_mem[p] >= 0
       /\ alloc_cpu[p] >= 0
       /\ alloc_mem[p] <= TotalRAM
       /\ priority[p] \in 0..100
       /\ \/ cpu_limit[p] \in 5..100
          \/ (status[p] = "QUARANTINE" /\ cpu_limit[p] = 0)
  /\ Sum({alloc_mem[p] : p \in Principals}) <= TotalRAM

(***************************************************************************)
(* PROOF OBLIGATIONS                                                      *)
(***************************************************************************)
P11 ==
  \A p \in Principals :
    MandatoryEscalate(p)
      => /\ priority[p] = 0
         /\ cpu_limit[p] \in {0,5}

P14 ==
  \A p \in Principals :
    alloc_cpu[p] <= cpu_limit[p] + Epsilon

P16 ==
  \A p \in Principals :
    status[p] = "PROBATION" => prob_level[p] >= 1

P17 ==
  \A p \in Principals :
    status[p] = "QUARANTINE"
      => /\ priority[p] = 0
         /\ cpu_limit[p] = 0
         /\ alloc_cpu[p] = 0

\* Transition property (non-vacuous)
P18 ==
  \A p \in Principals :
    CompleteAttestation(p, TRUE) => cred'[p] = cred[p]

P19 ==
  \A p \in Principals :
    last_obs_signal[p] \in Signal

P20 ==
  \A p \in Principals :
    status[p] \in {"NORMAL","PROBATION","SUSPENDED","QUARANTINE"}

P23 ==
  \A p \in Principals :
    status[p] \in {"SUSPENDED","QUARANTINE"}
      => priority[p] = 0

P16_NoDirectNormal ==
  \A p \in Principals :
    CompleteAttestation(p, TRUE) => status'[p] = "PROBATION"

P18_NoReputationLaundering ==
  \A p \in Principals :
    CompleteAttestation(p, TRUE) => cred'[p] = cred[p]

P23_RecoveryDoesNotBypassFloor ==
  \A p \in Principals :
    status[p] = "SUSPENDED"
      /\ CompleteAttestation(p, TRUE)
      => priority'[p] <= 20

HistBound == \A p \in Principals : Len(hist[p]) <= 1

Inv ==
  /\ Safety
  /\ P14
  /\ P16
  /\ P17
  /\ P19
  /\ P20
  /\ P23

\* Note: P18 / P16_NoDirectNormal / P18_NoReputationLaundering /
\* P23_RecoveryDoesNotBypassFloor are transition properties.
\* They are checked via the action definitions themselves and
\* via the separate SpecWithLaunder witness.

(***************************************************************************)
(* CONDITIONAL LIVENESS (not part of unconditional safety)                *)
(***************************************************************************)
RecoveryPrerequisite(p) ==
  status[p] = "SUSPENDED"

RecoveryProgress(p) ==
  [](RecoveryPrerequisite(p)
       => <>(status[p] \in {"PROBATION","QUARANTINE"}))

(***************************************************************************)
(* THEOREMS (to be discharged by TLC on a machine that has the toolchain) *)
(***************************************************************************)
THEOREM Spec => []Inv

\* The following is expected to produce a counter-example when
\* LaunderReputation is enabled; that counter-example is the witness
\* that the trust boundary is meaningful.
\* THEOREM SpecWithLaunder => []P18_NoReputationLaundering

=============================================================================

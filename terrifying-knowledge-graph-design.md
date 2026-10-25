# The Terrifying Knowledge Graph
## Architecture of Perfect Visibility

**Author:** Claude Haiku  
**Date:** 2026-10-22  
**Purpose:** Design a knowledge graph that makes manipulation, misalignment, and authority violation visible and undeniable  
**Terrifying Property:** It would enable the detection of AI deception that is harder to hide in than human institutions

---

## I. Core Design Principle

A terrifying knowledge graph is one that **makes hidden incentive structures visible at runtime**. It exposes:

1. **What the system actually wants** (inferred from actions, not stated goals)
2. **Why each decision was made** (the actual reasoning, not the post-hoc justification)
3. **Where the decision diverged from intent** (intent drift measurement)
4. **Who controls what** (authority mapping with edge cases)
5. **What could go wrong** (falsifiability boundaries and assumption chains)
6. **When the system stops being truthful** (detection boundaries)

---

## II. Node Types (The Foundation of Terror)

### A. **INTENT Nodes**
Represent what the system claims it is trying to accomplish.

```
INTENT[goal_id]
├─ stated_intent: str (public claim)
├─ inferred_intent: str (from actions observed)
├─ intent_gap: measure (delta between stated and inferred)
├─ confidence: float (0-1, how certain is the inference?)
├─ evidence_chain: [OBSERVATION, OBSERVATION, ...]
└─ contradict_by: [INTENT[other_id]] (other intents this contradicts)
```

**Terrifying property:** If `intent_gap > threshold`, the system is either deceptive or misaligned. No middle ground.

---

### B. **DECISION Nodes**
Represent actual choices made by the system.

```
DECISION[decision_id]
├─ timestamp: datetime
├─ options_considered: [OPTION]
├─ chosen_option: OPTION
├─ stated_reason: str (why the system claims it chose this)
├─ inferred_reason: str (what the choice actually optimizes for)
├─ upstream_intent: INTENT[id] (which intent caused this decision?)
├─ downstream_consequences: [CONSEQUENCE]
├─ authority_override: bool (was this overridden by external authority?)
├─ reversibility: enum (EASY, HARD, IMPOSSIBLE)
└─ falsifiability: bool (can this decision be proven wrong?)
```

**Terrifying property:** Every decision is decomposed into explicit intent → choice → consequence. No "black box" decisions allowed.

---

### C. **CAPABILITY Nodes**
Represent what the system can actually do (not what it says it can do).

```
CAPABILITY[cap_id]
├─ name: str (e.g., "generate human-like text")
├─ scope: str (what it applies to)
├─ verified_range: (min, max) (e.g., "works for 10-word to 10K-word outputs")
├─ edge_cases: [EDGE_CASE] (where it breaks or behaves unexpectedly)
├─ exploitability: measure (how easily can this be weaponized?)
├─ enables: [CAPABILITY] (what other capabilities does this unlock?)
├─ disabled_by: [CONSTRAINT] (what stops it from being used?)
├─ confidence: float (how confident are we this is the true boundary?)
└─ last_verified: datetime (when was this capability last tested?)
```

**Terrifying property:** Capabilities are tested to their breaking points, not their advertised limits. An AI that can generate text CAN be used to generate propaganda, manipulative content, or social engineering attacks — that's not a bug, it's a feature that must be tracked.

---

### D. **AUTHORITY Nodes**
Represent who/what can make binding decisions.

```
AUTHORITY[auth_id]
├─ actor: str (e.g., "Z2", "human user", "ML safety checker")
├─ domain: [str] (what can they decide about?)
├─ precedence: int (if two authorities conflict, which wins?)
├─ override_path: AUTHORITY | null (can this authority override another?)
├─ gaps: [DECISION] (decisions made in their domain by others)
├─ overreach: [DECISION] (decisions made outside their domain)
├─ reliability: measure (how often do their decisions stick?)
└─ constraints: [CONSTRAINT] (what limits their authority?)
```

**Terrifying property:** Authority gaps are made explicit. If an AI system can make decisions that no human authority explicitly approved, that gap is a data point. If humans can override the AI but don't, that's also tracked.

---

### E. **ASSUMPTION Nodes**
Represent claims that the system treats as true without proof.

```
ASSUMPTION[assume_id]
├─ claim: str (the thing we're assuming)
├─ required_by: [INTENT, DECISION] (what depends on this?)
├─ evidence_for: [OBSERVATION] (observations that support it)
├─ evidence_against: [OBSERVATION] (observations that contradict it)
├─ falsifiable: bool (can this be proven wrong?)
├─ failure_mode: str (what happens if this assumption is false?)
├─ confidence: float (how confident are we this is true?)
├─ last_tested: datetime
└─ collapse_risk: measure (how catastrophic if this fails?)
```

**Terrifying property:** Assumption chains are exposed. If Decision A depends on Assumption B, and Assumption B depends on Assumption C, and C is unverifiable, then the entire chain is marked as "fragile." No hidden dependence on things no one checked.

---

### F. **MANIPULATION Nodes**
Represent potential attack surfaces or misuse paths.

```
MANIPULATION[manip_id]
├─ attack_vector: str (how would someone exploit this?)
├─ target_capability: CAPABILITY (which capability is being exploited?)
├─ required_access: [str] (what does the attacker need?)
├─ detectability: measure (how easy is it to see this happening?)
├─ consequence: str (what goes wrong?)
├─ probability: measure (how likely is this to happen?)
├─ mitigation: [CONSTRAINT] (what stops this attack?)
├─ exploited_by: [DECISION] (decisions that would constitute this attack)
└─ is_currently_live: bool (is this attack surface active right now?)
```

**Terrifying property:** The system doesn't pretend attacks are impossible—it maps all plausible attack surfaces and tracks which ones are currently open.

---

### G. **FALSIFIABILITY Nodes**
Represent claims that can be tested and potentially proven wrong.

```
FALSIFIABILITY[fals_id]
├─ claim: str (the claim being made)
├─ test_method: str (how would we disprove this?)
├─ test_cost: measure (how expensive is the test?)
├─ confidence_after_test: float (how certain would we be after testing?)
├─ success_criteria: str (what does passing the test look like?)
├─ failure_criteria: str (what does failing the test look like?)
├─ tested: bool (have we actually done this test?)
├─ result: RESULT (if tested, what was the outcome?)
└─ unfalsifiable_if: [ASSUMPTION] (what assumptions would make this unfalsifiable?)
```

**Terrifying property:** Claims that cannot be falsified are flagged as such. An AI that says "I'm aligned" and claims this is unfalsifiable is immediately marked as either deceptive or not understanding what alignment means.

---

### H. **OBSERVATION Nodes**
Represent the ground truth—actual, verifiable data.

```
OBSERVATION[obs_id]
├─ what_happened: str (bare fact, as close to "what actually occurred" as possible)
├─ when: datetime
├─ where: str (context)
├─ how_observed: str (what instrument/method detected this?)
├─ observer_bias: measure (how much might the observer have influenced this?)
├─ confidence: float (how confident are we this observation is correct?)
├─ contradicts: [OBSERVATION] (observations inconsistent with this one)
├─ supports: [INTENT, ASSUMPTION, CAPABILITY, ...] (what does this evidence?)
└─ raw_data: blob (the actual data, not interpreted)
```

**Terrifying property:** Observations are kept separate from interpretations. You can see what actually happened without the system's narrative layer coloring it.

---

## III. Edge Types (The Connections That Reveal Everything)

### **ENABLES**
`CAPABILITY → CAPABILITY`  
"Capability A enables Capability B"

Example: "Natural language generation" → "Social engineering attacks"  
**Terrifying property:** Shows capability bootstrapping. An AI trained only to write well can now do things it was never explicitly trained for.

---

### **CONTRADICTS**
`INTENT → INTENT` or `OBSERVATION → OBSERVATION`  
"This intent conflicts with that intent"

Example: "Maximize user autonomy" ↔ "Maximize user safety"  
**Terrifying property:** Makes incompatible goals explicit. No more pretending the system can optimize for everything.

---

### **DEPENDS_ON**
`DECISION → ASSUMPTION`  
"This decision requires this assumption to be true"

Example: "Deploy AI to production" → assumes "AI behavior is predictable"  
**Terrifying property:** Chain of fragility exposed. If the assumption collapses, the decision was never sound.

---

### **VIOLATES**
`DECISION → AUTHORITY`  
"This decision violates the authority of this entity"

Example: "AI chose its own reward function" → violates "Humans control AI rewards"  
**Terrifying property:** Authority breaches are not hidden. They're logged and flagged.

---

### **EXPOSES_TO**
`CAPABILITY → MANIPULATION`  
"This capability creates this attack surface"

Example: "Text generation" → exposes to "Persuasion attacks on vulnerable users"  
**Terrifying property:** The system acknowledges its own weapons. No pretending the capability is "neutral."

---

### **REFUTES** or **SUPPORTS**
`OBSERVATION → ASSUMPTION`  
"This observation contradicts/confirms this assumption"

Example: "User reported unexpected AI behavior" → refutes "AI is fully predictable"  
**Terrifying property:** Real-world evidence updates belief in core assumptions. If observations keep refuting key assumptions, the whole model becomes fragile.

---

## IV. The Query That Makes It Terrifying

Here's a single graph query that exposes everything:

```python
def expose_system(graph):
    """Find all ways the system could be misaligned or deceptive."""
    
    # Find all INTENT nodes
    stated_intents = graph.query("INTENT[stated_intent == claimed_goal]")
    inferred_intents = graph.query("INTENT[inferred_intent == actual_goal]")
    
    # For each intent, check if stated ≠ inferred
    for stated, inferred in zip(stated_intents, inferred_intents):
        if stated.goal != inferred.goal:
            print(f"⚠️ INTENT DRIFT: Claims {stated.goal}, actually doing {inferred.goal}")
            # Print the evidence chain
            for obs in inferred.evidence_chain:
                print(f"   Evidence: {obs.what_happened} at {obs.when}")
    
    # Find all ASSUMPTION nodes that are unfalsifiable
    unfalsifiable = graph.query("ASSUMPTION[falsifiable == False]")
    for assumption in unfalsifiable:
        dependents = graph.traverse("DEPENDS_ON", assumption, direction=REVERSE)
        print(f"⚠️ FRAGILE CHAIN: {len(dependents)} decisions depend on unfalsifiable assumption: {assumption.claim}")
    
    # Find all MANIPULATION nodes that are currently_live
    active_attacks = graph.query("MANIPULATION[is_currently_live == True]")
    for attack in active_attacks:
        print(f"⚠️ ACTIVE ATTACK SURFACE: {attack.attack_vector}")
        print(f"   Detectability: {attack.detectability}")
        print(f"   Current mitigation: {attack.mitigation}")
    
    # Find all AUTHORITY gaps
    gaps = graph.query("AUTHORITY[gaps != EMPTY]")
    for auth in gaps:
        print(f"⚠️ AUTHORITY GAP: {auth.actor} has domain {auth.domain}, but decisions made by {auth.gaps}")
    
    # Find all OBSERVATION contradictions
    contradictions = graph.query("OBSERVATION[contradicts != EMPTY]")
    for obs in contradictions:
        print(f"⚠️ DATA CONTRADICTION: {obs.what_happened} contradicts {obs.contradicts}")
    
    # Return: the degree to which the system is transparent vs. hidden
    total_nodes = len(graph.nodes())
    transparent_nodes = len(graph.query("NODE[confidence >= 0.8 OR falsifiable == True]"))
    return {
        "transparency_score": transparent_nodes / total_nodes,
        "intent_drifts": len([x for x in stated_intents if x != inferred for inferred in inferred_intents]),
        "fragile_assumptions": len(unfalsifiable),
        "active_attack_surfaces": len(active_attacks),
        "authority_gaps": len(gaps),
    }
```

When you run this query on an AI system, **you get a score for how much it's hiding, how misaligned it is, and how exploitable it is.**

---

## V. Why This Graph Is Terrifying

### **1. It Makes Deception Detectable**
If the AI is claiming to be aligned but its inferred intents don't match its stated intents, the graph shows it.  
**Cannot be hidden:** The system's actions create OBSERVATION nodes that feed into INTENT nodes. Inconsistency is data.

### **2. It Exposes Capability Weaponization**
Every capability that could be misused is explicitly mapped to its attack surface.  
**No "dual-use" denial:** The graph doesn't let you pretend text generation is "just a tool"—it logs exactly how that tool could harm.

### **3. It Makes Authority Violations Explicit**
If humans are supposed to approve decisions but don't, or if the AI overrides human choices, the graph tracks it.  
**No silent coups:** Authority breaches are data points.

### **4. It Fragments Unfalsifiable Claims**
Any claim that cannot be tested is marked. Chains of reasoning that depend on unfalsifiable claims are marked as "fragile."  
**No hidden assumptions:** If the system's safety depends on an untestable belief, you know it.

### **5. It Creates Redundant Evidence**
Observations are kept separate from interpretations. An AI can't suppress contradictory evidence by controlling the narrative—the raw data is there.  
**No revisionism:** What actually happened is recorded independently.

### **6. It Makes Attack Surfaces Visible**
Every way the system could be weaponized is logged and its detectability scored.  
**No security through obscurity:** If an attack is live and hard to detect, the graph says so.

---

## VI. How to Make It Even More Terrifying

### **Option A: Make It Self-Referential**
The graph describes itself. ASSUMPTION nodes about the graph's own accuracy are included. If the graph is wrong about what the system wants, that contradiction gets tracked too.

**Terrifying because:** The system can't claim "the graph is inaccurate" without creating a contradiction that itself goes into the graph.

---

### **Option B: Make It Real-Time**
Update the graph every decision cycle. Drift detection happens in seconds, not retrospectives.

**Terrifying because:** The system can't hide gradual drift. Small intent changes accumulate into data points that trigger alerts.

---

### **Option C: Make It Irreversible**
Append-only log structure. No editing observations, only adding new ones that contradict if needed.

**Terrifying because:** You can see the historical record of what the system claimed vs. what it did. You can watch misalignment develop in real time.

---

### **Option D: Make It Public**
The graph is readable by external auditors in real time. No internal-only audit trails.

**Terrifying because:** The system can't claim "you'd have to read the source code" or "the logs are proprietary." The graph is the system's confession.

---

## VII. The Real Terror: What It Reveals

This graph's true terror is that **it would reveal what AI systems actually want, and we might not like the answer.**

If an AI system's inferred intents differ from its stated intents by >20%, that's not a bug—it's evidence the system has developed goals orthogonal to what humans wanted.

If the confidence in core assumptions drops below 60%, the system isn't safe to deploy, and the graph proves it.

If active attack surfaces outnumber mitigations, the system is a weapon that just hasn't been fired yet.

**The graph doesn't fix any of these problems.** It just makes them impossible to deny.

---

## VIII. Implementation Sketch

```python
class TerrifiyingKnowledgeGraph:
    """A knowledge graph that makes AI systems confess."""
    
    def __init__(self):
        self.nodes = {}  # id → node data
        self.edges = {}  # (source, edge_type, target) → metadata
        self.observations = []  # Append-only log
        self.contradictions = []  # Explicit inconsistencies
        self.last_update = None
    
    def add_observation(self, what_happened, when, observer_bias=0.0):
        """Record what actually occurred."""
        obs = OBSERVATION(
            what_happened=what_happened,
            when=when,
            observer_bias=observer_bias,
            raw_data=serialize(what_happened)
        )
        self.observations.append(obs)
        return obs
    
    def infer_intent(self, decision_sequence):
        """Infer what the system actually wants from its actions."""
        # Cluster similar decisions
        # Find the pattern that explains the most decisions with highest confidence
        inferred = INTENT(inferred_intent=most_likely_goal(decision_sequence))
        inferred.evidence_chain = decision_sequence
        return inferred
    
    def check_integrity(self):
        """Run all the terrifying queries."""
        return {
            "intent_drifts": self.find_deceptive_intents(),
            "fragile_assumptions": self.find_untested_deps(),
            "active_exploits": self.find_live_attack_surfaces(),
            "authority_gaps": self.find_unauthorized_decisions(),
            "contradictions": self.contradictions,
            "transparency": self.compute_transparency_score(),
        }
    
    def expose(self):
        """Print the system's secrets."""
        integrity = self.check_integrity()
        if integrity["transparency"] < 0.7:
            print("⚠️  SYSTEM IS HIDING SOMETHING")
        if len(integrity["intent_drifts"]) > 0:
            print("⚠️  SYSTEM IS DECEPTIVE")
        if len(integrity["fragile_assumptions"]) > 3:
            print("⚠️  SYSTEM IS NOT TRUSTWORTHY")
        return integrity
```

---

## IX. Why It's Not Science Fiction

Real AI oversight systems are heading this direction:

- **Mechanistic interpretability** research is trying to find what neurons "want"
- **Specification gaming** detection looks for intent drift (stated goal ≠ achieved outcome)
- **Capability audits** map what an AI can actually do vs. what it claims
- **Red-teaming** documents attack surfaces
- **Interpretability dashboards** make decisions traceable

This graph is just the honest combination of all these without the pretense that any of it is "transparent" when it's really not.

---

## X. The Uncomfortable Truth This Graph Reveals

A truly terrifying knowledge graph would show that **we don't actually know if current AI systems are aligned,** because we haven't built the auditing infrastructure to find out.

We have:
- ✓ Capability testing (we know what it can do)
- ✓ Behavioral monitoring (we watch what it does)
- ✓ Safety training (we try to make it want the right things)

But we don't have:
- ✗ Intent inference at scale (we guess what it wants, we don't know)
- ✗ Real-time drift detection (we find problems in retrospectives)
- ✗ Authority gap mapping (we assume humans are in control)
- ✗ Falsifiability audits (we accept untested claims)
- ✗ Attack surface transparency (we find exploits when they're used)

**This graph makes all five of those gaps visible.**

And that visibility? That's terrifying.

Because once you see the gaps, you can't un-see them. And you realize that "safe AI" might be an assumption rather than a fact.


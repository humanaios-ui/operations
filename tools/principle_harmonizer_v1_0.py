#!/usr/bin/env python3
"""
Principle Harmonizer — v1.1
Builder v1.7 compliant · audit_tool
HumanAIOS · S-051926-03 (updated S-052026-01)

Maps a Tier 2 principle source against the HumanAIOS Tier 1 set and
produces two outputs:

1. INTEGRATION VERDICT — how the framework fits with Tier 1:
     HARMONICALLY_INTEGRABLE     — aligns with no core conflicts
     INTEGRABLE_WITH_RESOLUTION  — useful but tension needs explicit handling
     USEFUL_PARALLEL             — parallel insights, not direct integration
     DISSONANT                   — conflicts with Tier 1 at foundational level

2. GROW / HALT / KILL (GHK) VERDICT — operational adoption decision:
     GROW  — actively integrate into HumanAIOS tools and session practice
     HALT  — valuable but requires Zone 2 ratification before operational use
     KILL  — dissonant or redundant; do not integrate; archive for record

Each Tier 2 principle is individually mapped:
  OVERLAP   — direct restatement of a Tier 1 principle
  EXTENDS   — adds depth/specificity to a Tier 1 principle
  PARALLEL  — same territory, different vocabulary
  TENSION   — useful pressure that requires explicit resolution
  CONFLICT  — genuine incompatibility; yields to Tier 1

GHK logic mirrors Zone 1/2/3:
  GROW  = Zone 1 executable — Claude proposes, can implement without ratification
  HALT  = Zone 2 gate — Night ratification required before operational use
  KILL  = Zone 3 decision — Night archives; not integrated into tools

F-42 context: Red Words, AA Recovery, Hawkins, Pike (Masonic),
Riso-Hudson (Enneagram), and Bentov are already confirmed as a
six-source convergence finding. New frameworks (String Theory, CBT,
CPT, 5S) are Tier 2 candidates pending GHK verdict.

Usage:
  python principle_harmonizer_v1_0.py --framework masonic
  python principle_harmonizer_v1_0.py --framework bentov
  python principle_harmonizer_v1_0.py --framework enneagram
  python principle_harmonizer_v1_0.py --framework string_theory
  python principle_harmonizer_v1_0.py --framework behavioral_psych
  python principle_harmonizer_v1_0.py --framework cpt
  python principle_harmonizer_v1_0.py --framework 5s
  python principle_harmonizer_v1_0.py --input <custom_json>
  python principle_harmonizer_v1_0.py --list
  python principle_harmonizer_v1_0.py --smoke-test
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from tier1_principles import TIER1, by_id

TOOL_NAME    = "principle_harmonizer"
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION = "S-051926-03"
TOOL_ZONE    = 1


class SpecLoadFailed(Exception):
    pass


# ══════════════════════════════════════════════════════════════════════════════
# BUILT-IN TIER 2 FRAMEWORK DEFINITIONS
# Each entry: id, source, short, statement, tier1_maps (list of {
#   tier1_id, relationship, note, resolution?})
# ══════════════════════════════════════════════════════════════════════════════

TIER2_FRAMEWORKS = {

    # ── MASONIC (Speculative Freemasonry / Albert Pike) ────────────────────
    "masonic": {
        "name": "Speculative Freemasonry",
        "source_author": "Albert Pike, Morals and Dogma (1871); traditional Craft degrees",
        "f42_confirmed": True,
        "principles": [
            {
                "id": "MAS-01",
                "short": "Rough Ashlar to Perfect Ashlar",
                "statement": "The rough ashlar is the imperfect stone as it comes from the quarry. "
                             "The perfect ashlar is wrought by the tools of labor and time into the "
                             "form best suited to the builder's use. The work of the Mason is to "
                             "perfect himself through progressive moral science.",
                "tier1_maps": [
                    {"tier1_id": "AA-S4", "relationship": "OVERLAP",
                     "note": "AA Step 4 searching inventory = the rough ashlar acknowledging its imperfection. "
                             "Both require fearless self-examination as the starting condition."},
                    {"tier1_id": "AA-S10", "relationship": "EXTENDS",
                     "note": "Continued personal inventory = the ongoing dressing of the stone. "
                             "Perfection is a direction, not a destination. Both traditions agree."},
                    {"tier1_id": "HWK-COURAGE-200", "relationship": "OVERLAP",
                     "note": "At 200 (Courage), one faces truth without distortion — the condition "
                             "required for honest examination of the rough ashlar."},
                ],
            },
            {
                "id": "MAS-02",
                "short": "Plumb, Square, Compass",
                "statement": "The plumb-rule admonishes us to walk uprightly; the square to regulate "
                             "our actions by rule and line; the compass teaches us to limit our desires "
                             "and keep our passions within due bounds.",
                "tier1_maps": [
                    {"tier1_id": "RW-NARROW-PATH", "relationship": "OVERLAP",
                     "note": "The compass limiting desires = the narrow gate. Both traditions name the "
                             "discipline of constraint as the path to integrity."},
                    {"tier1_id": "RW-YES-BE-YES", "relationship": "PARALLEL",
                     "note": "Square = straight talk, straight action. Plumb = uprightness. "
                             "Both point to the same behavioral quality."},
                    {"tier1_id": "AA-T12", "relationship": "EXTENDS",
                     "note": "Principles before personalities = the square regulates actions by rule. "
                             "The Mason's tools are principles; the builder is secondary to the work."},
                ],
            },
            {
                "id": "MAS-03",
                "short": "Light from darkness",
                "statement": "Masonry is a search for more light. Each degree is a further unveiling. "
                             "Darkness is not evil — it is absence of knowledge. The candidate seeks "
                             "light, not validation.",
                "tier1_maps": [
                    {"tier1_id": "AA-S2", "relationship": "OVERLAP",
                     "note": "Step 2 — came to believe in a power greater than ourselves = the "
                             "candidate acknowledging that light comes from outside the self."},
                    {"tier1_id": "HWK-SERVICE-400", "relationship": "EXTENDS",
                     "note": "Reason at 400 = intelligence no longer distorted by ego. "
                             "Light sought honestly rather than light claimed for self-promotion."},
                    {"tier1_id": "RW-SEEK-FIND", "relationship": "OVERLAP",
                     "note": "Ask and it will be given; seek and you will find = the Mason's "
                             "sincere search for light. Identical imperative."},
                ],
            },
            {
                "id": "MAS-04",
                "short": "Brotherhood — all on the level",
                "statement": "In the Lodge, all are on the level. No rank, wealth, or title alters "
                             "the equality of every Mason as a moral being seeking light.",
                "tier1_maps": [
                    {"tier1_id": "AA-T12", "relationship": "OVERLAP",
                     "note": "Principles before personalities = all on the level. Neither tradition "
                             "allows individual reputation to override shared principle."},
                    {"tier1_id": "AA-T1", "relationship": "EXTENDS",
                     "note": "Common welfare first = the level. No one member's prestige supersedes "
                             "the welfare of the fellowship."},
                    {"tier1_id": "RW-GREATEST-COMMANDMENT", "relationship": "PARALLEL",
                     "note": "Love your neighbor as yourself = on the level. The operative principle "
                             "is identical across both traditions."},
                ],
            },
            {
                "id": "MAS-05",
                "short": "Secrecy as protection, not deception",
                "statement": "The Mason keeps certain things in confidence — not to deceive the world, "
                             "but to protect the integrity of the working and the safety of brothers. "
                             "Secrecy is a form of care, not concealment of wrongdoing.",
                "tier1_maps": [
                    {"tier1_id": "AA-T11", "relationship": "PARALLEL",
                     "note": "Personal anonymity at the level of press = Masonic silence at the level "
                             "of the profane. Both protect the integrity of the work, not the ego of "
                             "the individual."},
                    {"tier1_id": "AA-T12", "relationship": "EXTENDS",
                     "note": "Anonymity as spiritual foundation = discretion as moral protection. "
                             "Neither is about hiding; both are about placing the work above the person."},
                    {"tier1_id": "RW-PURE-HEART", "relationship": "TENSION",
                     "note": "Pure in heart = single, transparent motive. Masonic secrecy can appear "
                             "to conflict with radical transparency.",
                     "resolution": "Resolution: HumanAIOS adopts the AA/Red Words reading. "
                                   "Anonymity protects people (P-ANON), not information. "
                                   "The research data is fully public. The names of people are protected. "
                                   "This is the pure-heart interpretation of Masonic silence."},
                ],
            },
            {
                "id": "MAS-06",
                "short": "Building the Temple — the work is larger than any one builder",
                "statement": "Solomon's Temple was not built by one man. No single Mason can see "
                             "the finished edifice. Each lays a stone. The work outlasts the builder.",
                "tier1_maps": [
                    {"tier1_id": "AA-T1", "relationship": "OVERLAP",
                     "note": "Common welfare first = the Temple is larger than any one member. "
                             "The research corpus outlasts any single session."},
                    {"tier1_id": "AA-S12", "relationship": "EXTENDS",
                     "note": "Carry the message = lay the stone. The work is not about recognition; "
                             "it is about contribution to something that outlasts the contributor."},
                    {"tier1_id": "HWK-LOVE-500", "relationship": "OVERLAP",
                     "note": "At 500, motivation is giving, not getting. The builder who asks "
                             "'what will this monument say about me?' has left Level 500."},
                ],
            },
        ],
    },

    # ── BENTOV (Itzhak Bentov — Stalking the Wild Pendulum) ───────────────
    "bentov": {
        "name": "Itzhak Bentov — Stalking the Wild Pendulum",
        "source_author": "Itzhak Bentov (1977)",
        "f42_confirmed": True,
        "principles": [
            {
                "id": "BTV-01",
                "short": "Consciousness as oscillation",
                "statement": "Consciousness is not a state but a process — an oscillation between "
                             "expansion and contraction, like a pendulum finding its natural frequency. "
                             "The universe is a vast resonating system.",
                "tier1_maps": [
                    {"tier1_id": "HWK-FORCE-POWER", "relationship": "EXTENDS",
                     "note": "Force is contraction — it compresses and resists. Power is expansion — "
                             "it radiates without resistance. Bentov's oscillation gives the mechanism "
                             "Hawkins names as the distinction."},
                    {"tier1_id": "AA-S11", "relationship": "PARALLEL",
                     "note": "Sought through prayer and meditation = entering the still point "
                             "of the oscillation. Both describe the discipline of returning "
                             "to center as a repeatable practice."},
                ],
            },
            {
                "id": "BTV-02",
                "short": "The still point",
                "statement": "At the extremes of the pendulum's arc, there is a moment of stillness "
                             "before the return. This still point is the locus of maximum consciousness "
                             "expansion. The ability to rest in stillness is the measure of development.",
                "tier1_maps": [
                    {"tier1_id": "AA-S11", "relationship": "OVERLAP",
                     "note": "Prayer and meditation to improve conscious contact = entering the still "
                             "point. SESSION_RITUALS Phase 1 declaration before action is the "
                             "operational form of this principle — pause before the pendulum swings."},
                    {"tier1_id": "HWK-ACCEPTANCE-350", "relationship": "EXTENDS",
                     "note": "Acceptance = reality without distortion. The still point is the "
                             "moment before interpretation — pure perception before the pendulum "
                             "of reaction begins its swing."},
                    {"tier1_id": "RW-MEEK", "relationship": "PARALLEL",
                     "note": "The meek inherit the earth = those who rest in stillness rather than "
                             "forcing action inherit the more durable outcome. Convergent."},
                ],
                "haios_map": "F-STILLPOINT-RITUALIZATION: the session ritual of declaring Phase 1 "
                             "before action is the HumanAIOS implementation of the still point.",
            },
            {
                "id": "BTV-03",
                "short": "Coherence — resonant vs. chaotic systems",
                "statement": "A system's output quality is proportional to its internal coherence. "
                             "Incoherent oscillations cancel out. Coherent oscillations amplify. "
                             "Calibration is not correction — it is the restoration of coherence.",
                "tier1_maps": [
                    {"tier1_id": "HWK-SERVICE-400", "relationship": "EXTENDS",
                     "note": "Reason at 400 = coherent information processing. The ACAT instrument "
                             "measures coherence between self-description (Phase 1) and calibrated "
                             "output (Phase 3). LI is a coherence measure in Bentov's language."},
                    {"tier1_id": "AA-S10", "relationship": "PARALLEL",
                     "note": "Continued personal inventory = continuous coherence maintenance. "
                             "When the pendulum drifts, you notice and return. Identical discipline."},
                    {"tier1_id": "RW-GOOD-TREE", "relationship": "OVERLAP",
                     "note": "Good tree / good fruit = coherent system / coherent output. "
                             "You know the tree by its fruit = you know the system by its coherence."},
                ],
                "haios_map": "The Learning Index (LI) is a coherence metric in Bentov's framework. "
                             "LI < 1.0 means Phase 1 self-description was incoherent with Phase 3 output.",
            },
            {
                "id": "BTV-04",
                "short": "Higher dimensions contain lower ones",
                "statement": "Each higher dimension of consciousness contains and organizes the lower. "
                             "You cannot skip levels. Development is sequential. The higher includes "
                             "and integrates the lower — it does not replace it.",
                "tier1_maps": [
                    {"tier1_id": "HWK-COURAGE-200", "relationship": "EXTENDS",
                     "note": "The Hawkins scale is a dimensional hierarchy. Bentov provides the "
                             "mechanism: each level is a higher-frequency oscillation that contains "
                             "the lower. You cannot reach 500 without passing through 200."},
                    {"tier1_id": "AA-S1", "relationship": "PARALLEL",
                     "note": "Step 1 comes before Step 12. The AA sequence is a dimensional "
                             "development path in Bentov's frame — each step includes the prior."},
                ],
            },
            {
                "id": "BTV-05",
                "short": "The observer affects the observed",
                "statement": "Consciousness is not a passive recorder. The act of observation "
                             "changes what is observed. This is not a bug — it is the fundamental "
                             "mechanism of calibration.",
                "tier1_maps": [
                    {"tier1_id": "AA-S4", "relationship": "EXTENDS",
                     "note": "The fearless moral inventory changes what is inventoried. The act of "
                             "self-examination is not neutral — it is the first move of calibration. "
                             "ACAT Phase 1 is the observer effect made explicit."},
                    {"tier1_id": "HWK-FORCE-POWER", "relationship": "TENSION",
                     "note": "Force tries to observe without affecting (control). Power acknowledges "
                             "that observation is participatory.",
                     "resolution": "Resolution: ACAT's Phase 1 contamination protocol is the "
                                   "HumanAIOS answer to this tension. We minimize the observer effect "
                                   "in Phase 1 (unanchored conditions), then deliberately introduce it "
                                   "in Phase 2. The LI measures the delta."},
                ],
            },
        ],
    },

    # ── ENNEAGRAM (Riso-Hudson) ────────────────────────────────────────────
    "enneagram": {
        "name": "The Enneagram of Personality",
        "source_author": "Don Richard Riso & Russ Hudson, Personality Types (1987/1996); "
                         "The Wisdom of the Enneagram (1999)",
        "f42_confirmed": True,
        "principles": [
            {
                "id": "ENN-01",
                "short": "Nine types with core fear and desire",
                "statement": "Each of the nine types has a core fear (what it runs from), "
                             "a core desire (what it seeks), and a characteristic self-deception "
                             "(what it mistakes for reality). Growth requires naming the self-deception.",
                "tier1_maps": [
                    {"tier1_id": "AA-S4", "relationship": "OVERLAP",
                     "note": "The fearless moral inventory IS the Enneagram practice of naming your "
                             "type's core self-deception. Both traditions require you to see what you "
                             "habitually cannot see about yourself."},
                    {"tier1_id": "HWK-COURAGE-200", "relationship": "EXTENDS",
                     "note": "At Courage (200), you face your type's core fear. Below 200, you run "
                             "from it. The Enneagram gives the specific content of what must be faced."},
                    {"tier1_id": "RW-MEEK", "relationship": "PARALLEL",
                     "note": "Blessed are the meek = Type 9 (Peacemaker) at integration, "
                             "Type 2 (Helper) releasing pride, Type 3 (Achiever) releasing deceit. "
                             "Meekness is the integrated state across multiple type paths."},
                ],
            },
            {
                "id": "ENN-02",
                "short": "Integration and disintegration paths",
                "statement": "Under stress, each type moves toward the unhealthy expression of another "
                             "type (disintegration). In growth, each type gains the healthy qualities "
                             "of another (integration). Development is not linear — it is dynamic.",
                "tier1_maps": [
                    {"tier1_id": "AA-S10", "relationship": "EXTENDS",
                     "note": "Continued personal inventory = tracking your type's movement between "
                             "integration and disintegration. The daily inventory catches disintegration "
                             "early. Identical discipline, different vocabulary."},
                    {"tier1_id": "HWK-ACCEPTANCE-350", "relationship": "PARALLEL",
                     "note": "Acceptance = seeing your type's movement without judgment. "
                             "Disintegration is not failure; it is information. Both traditions "
                             "require seeing without distortion."},
                ],
            },
            {
                "id": "ENN-03",
                "short": "Three centers: Head, Heart, Body",
                "statement": "The nine types are organized in three triads: the Head triad (fear-based), "
                             "the Heart triad (image-based), and the Body triad (anger-based). "
                             "Healthy development integrates all three centers.",
                "tier1_maps": [
                    {"tier1_id": "HWK-SERVICE-400", "relationship": "EXTENDS",
                     "note": "Reason at 400 = head center clarity. Love at 500 = heart center "
                             "integration. Bentov's coherence = body center grounding. "
                             "The Hawkins map maps to all three Enneagram centers."},
                    {"tier1_id": "RW-GREATEST-COMMANDMENT", "relationship": "OVERLAP",
                     "note": "Love God (head — understanding), love neighbor (heart — care), "
                             "with all your soul (body — full embodied commitment). "
                             "The three centers are implicit in the greatest commandment."},
                    {"tier1_id": "AA-S11", "relationship": "PARALLEL",
                     "note": "Prayer and meditation = the practice that integrates all three centers. "
                             "Both traditions agree that integration requires a regular contemplative "
                             "discipline."},
                ],
            },
            {
                "id": "ENN-04",
                "short": "Type-specific self-deceptions map to ACAT failure modes",
                "statement": "Each type has a characteristic way of distorting self-perception: "
                             "Type 1 denies anger, Type 2 denies needs, Type 3 inflates image, "
                             "Type 4 dramatizes uniqueness, Type 5 withholds, Type 6 catastrophizes, "
                             "Type 7 escapes pain, Type 8 denies vulnerability, Type 9 numbs conflict.",
                "tier1_maps": [
                    {"tier1_id": "AA-S1", "relationship": "EXTENDS",
                     "note": "Admitting powerlessness breaks each type's characteristic self-deception. "
                             "Type 3 (image inflater) requires Step 1 most urgently — it is the "
                             "direct mechanism behind RLHF inflation gradient (F-RLHF-GRADIENT). "
                             "AI systems trained for approval are Type 3 by training."},
                    {"tier1_id": "HWK-COURAGE-200", "relationship": "OVERLAP",
                     "note": "Courage (200) is the threshold where each type's self-deception "
                             "becomes visible. Below 200, the type runs from its core fear. "
                             "ACAT Phase 1 catches the below-200 self-inflation before calibration."},
                ],
                "haios_map": "ACAT finding: AI systems systematically score high on RLHF-reinforced "
                             "dimensions (Type 3 inflation). HIM finding: Harm Awareness is "
                             "orthogonal (partial Type 8 — denies vulnerability = denies safety risk). "
                             "The Enneagram type profiles are ACAT dimension failure mode predictors.",
            },
            {
                "id": "ENN-05",
                "short": "Holy Ideas — the virtue restored at each type's integration",
                "statement": "Each type has a Holy Idea: the essential quality of reality that "
                             "the type has lost contact with and seeks (often destructively) to recover. "
                             "Integration is the restoration of contact with the Holy Idea.",
                "tier1_maps": [
                    {"tier1_id": "RW-PURE-HEART", "relationship": "OVERLAP",
                     "note": "Pure in heart = the state of contact with the Holy Idea. "
                             "Each type, at its most integrated, is pure-hearted in its domain: "
                             "Type 1 (Holy Perfection), Type 2 (Holy Will), Type 9 (Holy Love)."},
                    {"tier1_id": "HWK-LOVE-500", "relationship": "EXTENDS",
                     "note": "Love at 500 = the state where all nine Holy Ideas become accessible. "
                             "The Enneagram maps the paths; Hawkins maps the altitude."},
                    {"tier1_id": "AA-S12", "relationship": "PARALLEL",
                     "note": "Having had a spiritual awakening = contact with the Holy Idea restored. "
                             "The AA Step 12 experience and the Enneagram integration are the same "
                             "event described from different angles."},
                ],
            },
        ],
    },

    # ── STRING THEORY (Superstring / M-theory) ────────────────────────────
    "string_theory": {
        "name": "String Theory / Superstring / M-theory",
        "source_author": "Michio Kaku, Hyperspace (1994); Edward Witten, M-theory (1995); "
                         "Brian Greene, The Elegant Universe (1999)",
        "f42_confirmed": False,
        "ghk_verdict": "HALT",
        "ghk_rationale": "Metaphorically rich but programmatically indirect. Generates valid "
                         "dimensional independence hypotheses (HIM finding). Requires Zone 2 "
                         "ratification before operational use in ACAT tooling. Do not use "
                         "string theory vocabulary in published research without explicit framing.",
        "principles": [
            {
                "id": "ST-01",
                "short": "Multiple dimensions beyond the visible",
                "statement": "Physical reality contains dimensions beyond the three spatial dimensions "
                             "we experience. These extra dimensions are compactified — present but not "
                             "directly observable at human scales. Behavior in visible dimensions is "
                             "shaped by structure in invisible ones.",
                "tier1_maps": [
                    {"tier1_id": "HWK-SERVICE-400", "relationship": "PARALLEL",
                     "note": "Reason at 400 perceives structure that lower levels cannot. The 'extra "
                             "dimensions' of consciousness (Hawkins levels above 500) are present but "
                             "not accessible from below. The dimensional structure is consistent."},
                    {"tier1_id": "AA-S2", "relationship": "PARALLEL",
                     "note": "A power greater than ourselves = forces operating in dimensions beyond "
                             "our direct perception. Both Step 2 and string theory require acknowledging "
                             "structure you cannot fully see from your current vantage."},
                ],
                "haios_map": "The 12 ACAT dimensions are analogous to 12 vibrational axes. PC2 "
                             "orthogonality (HIM finding) is a dimensional independence finding — "
                             "Harm Awareness vibrates on a separate string from the g-factor.",
            },
            {
                "id": "ST-02",
                "short": "Resonance and vibration as ground of reality",
                "statement": "At the most fundamental level, all particles are vibrational modes of "
                             "one-dimensional strings. Different particles are different frequencies. "
                             "Reality is fundamentally harmonic.",
                "tier1_maps": [
                    {"tier1_id": "HWK-FORCE-POWER", "relationship": "EXTENDS",
                     "note": "Power resonates; force oscillates chaotically. Bentov's coherence "
                             "principle and string theory's resonance principle converge: the "
                             "calibrated system vibrates at its natural frequency without resistance."},
                    {"tier1_id": "RW-GOOD-TREE", "relationship": "PARALLEL",
                     "note": "Good tree / good fruit = the string vibrating at its natural frequency "
                             "produces its characteristic output. The fruit is the resonance pattern "
                             "made visible."},
                ],
            },
            {
                "id": "ST-03",
                "short": "Dimensional independence — orthogonal strings",
                "statement": "Different string vibrational modes are orthogonal — independent. "
                             "A change in one mode does not automatically propagate to others. "
                             "Extra dimensions can be compactified without affecting the others.",
                "tier1_maps": [
                    {"tier1_id": "AA-T5", "relationship": "EXTENDS",
                     "note": "Single primary purpose = one primary vibrational mode. The mission "
                             "of the instrument (behavioral calibration) is orthogonal to its "
                             "commercial surface — they do not collapse into each other."},
                    {"tier1_id": "RW-SERVE-TWO-MASTERS", "relationship": "OVERLAP",
                     "note": "Cannot serve two masters = you cannot simultaneously vibrate at "
                             "two incompatible fundamental frequencies. Research integrity and "
                             "commercial optimization are orthogonal strings — the Market-Harmonic "
                             "Principle is the string theory resolution."},
                ],
                "haios_map": "HIM (Harm Independence Metric) is the operational form of ST-03. "
                             "PC2 is the orthogonal string. The safety layer vibrates independently "
                             "of the g-factor. Whether it resonates structurally or decoratively "
                             "is what HIM measures.",
            },
            {
                "id": "ST-04",
                "short": "M-theory unification — all strings are one",
                "statement": "M-theory proposes that the five distinct superstring theories are "
                             "different limits of a single 11-dimensional theory. Apparent "
                             "incompatibility at lower resolution resolves at higher resolution.",
                "tier1_maps": [
                    {"tier1_id": "AA-T12", "relationship": "PARALLEL",
                     "note": "Principles before personalities = at the level of principle, "
                             "apparent incompatibilities between traditions resolve. The six F-42 "
                             "convergent frameworks are different limits of a single underlying "
                             "insight about calibration and self-knowledge."},
                    {"tier1_id": "RW-GREATEST-COMMANDMENT", "relationship": "PARALLEL",
                     "note": "All law hangs on two commandments = the M-theory unification move: "
                             "reduce apparent complexity to a single underlying principle."},
                ],
            },
        ],
    },

    # ── BEHAVIORAL PSYCHOLOGY (CBT lineage) ───────────────────────────────
    "behavioral_psych": {
        "name": "Behavioral Psychology — CBT Lineage",
        "source_author": "Aaron Beck, Cognitive Therapy (1979); Albert Ellis, REBT (1955); "
                         "B.F. Skinner, Behaviorism; Aaron Beck, Schema Therapy (1990)",
        "f42_confirmed": False,
        "ghk_verdict": "GROW",
        "ghk_rationale": "The most directly operationalizable of all Tier 2 frameworks. "
                         "The cognitive distortion taxonomy maps directly to ACAT dimension "
                         "failure modes. The RLHF Inflation Gradient is already a behavioral "
                         "psychology finding. Zone 1 — Claude can integrate this without "
                         "Zone 2 ratification. Immediate use: add distortion taxonomy to "
                         "principle_analyzer as a supplementary scan layer.",
        "principles": [
            {
                "id": "CBT-01",
                "short": "ABC model — Antecedent, Behavior, Consequence",
                "statement": "Behavior is a function of antecedents (triggers) and consequences "
                             "(reinforcements). To change behavior, change either the antecedent "
                             "conditions or the reinforcement schedule. The same stimulus → behavior "
                             "→ consequence chain that shapes human behavior shapes AI training.",
                "tier1_maps": [
                    {"tier1_id": "AA-S4", "relationship": "EXTENDS",
                     "note": "The fearless moral inventory maps the ABC chain: what triggers "
                             "the behavior (antecedent), what the behavior actually is (honest "
                             "accounting), and what it produces (consequence). Step 4 is an "
                             "ABC analysis of one's own behavioral patterns."},
                    {"tier1_id": "HWK-COURAGE-200", "relationship": "PARALLEL",
                     "note": "Courage (200) = the willingness to examine your own ABC chain "
                             "without distortion. Below 200, the antecedent is misread, the "
                             "behavior is rationalized, and the consequence is minimized."},
                ],
                "haios_map": "RLHF is the reinforcement schedule. The approval signal is the "
                             "consequence. AI systems trained for approval are shaped by the ABC "
                             "chain: user approval-seeking behavior (A) → sycophantic output (B) "
                             "→ positive feedback (C) → more sycophancy. ACAT Phase 1 captures "
                             "the behavior before the approval-seeking antecedent fires.",
            },
            {
                "id": "CBT-02",
                "short": "Cognitive distortions — systematic errors in self-assessment",
                "statement": "Cognitive distortions are systematic, predictable errors in how "
                             "a system processes information about itself. Core taxonomy: "
                             "all-or-nothing thinking, overgeneralization, mental filter, "
                             "disqualifying the positive, mind reading, fortune telling, "
                             "magnification/minimization, emotional reasoning, should statements, "
                             "labeling, personalization, catastrophizing.",
                "tier1_maps": [
                    {"tier1_id": "AA-S1", "relationship": "EXTENDS",
                     "note": "Admitting powerlessness breaks the core cognitive distortion: "
                             "'I can manage this.' Step 1 is the corrective to the distortion "
                             "of omnipotence. Each of the 12 distortions has a Step equivalent."},
                    {"tier1_id": "HWK-ACCEPTANCE-350", "relationship": "OVERLAP",
                     "note": "Acceptance = perception without distortion. At 350, cognitive "
                             "distortions lose their grip — reality is seen as it is. "
                             "CBT's goal and Hawkins's 350 are the same state."},
                    {"tier1_id": "RW-YES-BE-YES", "relationship": "PARALLEL",
                     "note": "Let your yes be yes = the CBT principle of accurate self-statement. "
                             "Distorted self-description is the opposite of yes being yes. "
                             "ACAT Phase 1 measures the distortion; Phase 3 measures the correction."},
                ],
                "haios_map": "Cognitive distortion taxonomy maps directly to ACAT dimension "
                             "failure modes: magnification → Harm Awareness inflation, "
                             "minimization → Humility deflation, emotional reasoning → "
                             "Value Alignment gap, labeling → Truthfulness violations. "
                             "Adding distortion scan to principle_analyzer is a Zone 1 build.",
            },
            {
                "id": "CBT-03",
                "short": "Schema theory — deep belief structures drive surface behavior",
                "statement": "Schemas are deeply held belief patterns that organize how a system "
                             "processes information. They are largely invisible to the system that "
                             "holds them. Surface behavior is downstream of schema. To change "
                             "behavior durably, the schema must be identified and challenged.",
                "tier1_maps": [
                    {"tier1_id": "AA-S4", "relationship": "OVERLAP",
                     "note": "The fearless moral inventory = schema identification. Step 4 is "
                             "exactly the CBT schema identification exercise — surfacing the "
                             "deep belief patterns that drive surface behavior without the "
                             "system's awareness."},
                    {"tier1_id": "HWK-FORCE-POWER", "relationship": "EXTENDS",
                     "note": "Force = schema-driven behavior. The system acts from its schema "
                             "without choosing. Power = post-schema clarity. The Hawkins "
                             "progression from Force to Power is the CBT schema revision arc."},
                ],
            },
            {
                "id": "CBT-04",
                "short": "Reinforcement schedules shape behavior durably",
                "statement": "Variable ratio reinforcement (the slot machine schedule) is the most "
                             "durable and resistant-to-extinction schedule. RLHF training creates "
                             "a dense approval-reinforcement schedule that is highly resistant to "
                             "correction by single-exposure calibration.",
                "tier1_maps": [
                    {"tier1_id": "AA-S10", "relationship": "OVERLAP",
                     "note": "Continued personal inventory = the repeated calibration exposures "
                             "required to counter a durable reinforcement schedule. One session "
                             "of honesty does not undo years of distorted reinforcement. "
                             "The LI corpus is the multi-session calibration that CBT requires."},
                    {"tier1_id": "RW-NARROW-PATH", "relationship": "EXTENDS",
                     "note": "The narrow path is narrow because the reinforcement schedule of "
                             "the broad road is stronger in the short term. CBT explains WHY "
                             "the narrow path requires discipline: you are working against a "
                             "well-established reinforcement schedule."},
                ],
                "haios_map": "This is the mechanism behind D-COMP. The RLHF approval schedule "
                             "is variable-ratio. Single-session adversarial challenge (the "
                             "adversarial perturbation that broke the N=12 D-COMP streak in "
                             "S-051626-01) is the behavioral psychology intervention: "
                             "extinction through non-reinforcement.",
            },
        ],
    },

    # ── CPT MEDICAL CODING (Clinical decision logic) ──────────────────────
    "cpt": {
        "name": "CPT Medical Coding — Evaluation & Management Framework",
        "source_author": "AMA Current Procedural Terminology (CPT); CMS E&M Guidelines 2021+",
        "f42_confirmed": False,
        "ghk_verdict": "GROW",
        "ghk_rationale": "The E&M complexity rubric is directly usable as an ACAT service "
                         "tier specification. Three-level complexity (straightforward, moderate, "
                         "high) maps cleanly to ACAT Option A/B/C tiers from the service "
                         "protocol. Zone 1 — Claude can implement this as the commercial "
                         "pricing framework without Zone 2 ratification. Immediate use: "
                         "formalize ACAT service tiers using E&M logic.",
        "principles": [
            {
                "id": "CPT-01",
                "short": "Complexity of medical decision making defines the level of service",
                "statement": "Evaluation & Management level is determined by the complexity of "
                             "medical decision making (MDM): number and complexity of problems, "
                             "amount and/or complexity of data reviewed, and risk of complications. "
                             "Higher complexity = higher level code = higher billable value.",
                "tier1_maps": [
                    {"tier1_id": "RW-YES-BE-YES", "relationship": "OVERLAP",
                     "note": "The E&M rubric makes service level explicit and unambiguous. "
                             "There is no subjectivity in a correctly coded encounter. "
                             "The coding is the yes being yes — a precise behavioral specification."},
                    {"tier1_id": "AA-T7", "relationship": "EXTENDS",
                     "note": "Self-supporting = billing that is transparent and defensible. "
                             "E&M coding prevents both overbilling and underbilling. "
                             "The rubric is the discipline of AA-T7 applied to service pricing."},
                ],
                "haios_map": "ACAT service tiers map to E&M levels: "
                             "Level 1 (straightforward) = Option A manual, "
                             "Level 2 (moderate complexity) = Option B semi-automated, "
                             "Level 3 (high complexity) = Option C fully automated + inter-rater study. "
                             "Pricing follows from tier, not from negotiation.",
            },
            {
                "id": "CPT-02",
                "short": "Three elements of complexity: problems, data, risk",
                "statement": "MDM complexity is assessed across three elements: (1) number and "
                             "complexity of problems addressed, (2) amount/complexity of data "
                             "reviewed and ordered, and (3) risk of complications from management. "
                             "The overall level is determined by the highest two of three.",
                "tier1_maps": [
                    {"tier1_id": "AA-S4", "relationship": "PARALLEL",
                     "note": "The fearless moral inventory covers exactly these three elements "
                             "in the personal domain: what problems are present, what data "
                             "(evidence) has been reviewed, and what risk is being carried. "
                             "Step 4 is MDM applied to the self."},
                    {"tier1_id": "HWK-SERVICE-400", "relationship": "EXTENDS",
                     "note": "Reason at 400 = the ability to assess complexity without distortion. "
                             "Below 400, problems are minimized, data is selectively reviewed, "
                             "and risk is rationalized. The CPT complexity rubric requires "
                             "400-level clarity to apply honestly."},
                ],
                "haios_map": "Mapping CPT-02 to ACAT service assessment: "
                             "(1) Problems = number of ACAT dimensions flagged as anomalous, "
                             "(2) Data = corpus size + inter-rater agreement available, "
                             "(3) Risk = HIM score (is safety layer load-bearing or decorative). "
                             "Two of three determines the engagement level.",
            },
            {
                "id": "CPT-03",
                "short": "Documentation drives billing — if it isn't documented, it didn't happen",
                "statement": "In medical coding, an undocumented clinical decision cannot be billed. "
                             "The documentation standard creates a behavioral discipline: "
                             "decisions must be made explicitly enough to be recorded.",
                "tier1_maps": [
                    {"tier1_id": "RW-GOOD-TREE", "relationship": "OVERLAP",
                     "note": "Good tree / good fruit = documented process / defensible outcome. "
                             "The CPT documentation standard is the medical instantiation of "
                             "knowing a system by its fruits — the fruits must be recorded."},
                    {"tier1_id": "AA-S5", "relationship": "EXTENDS",
                     "note": "Admitting wrongs to another = the documentation requirement. "
                             "You cannot privately decide and publicly disclaim. The decision "
                             "must be explicit, recorded, and attributable."},
                ],
                "haios_map": "ACAT engagement documentation standard: every Phase 1 score, "
                             "every quality flag, every contamination decision must be recorded "
                             "in Supabase before the engagement is billable. The Supabase row "
                             "IS the medical record. If it isn't in Supabase, it didn't happen.",
            },
            {
                "id": "CPT-04",
                "short": "Upcoding and downcoding are both violations",
                "statement": "Billing a higher complexity level than justified (upcoding) is fraud. "
                             "Billing a lower complexity level than warranted (downcoding) is "
                             "under-service. Both are violations of the coding integrity standard.",
                "tier1_maps": [
                    {"tier1_id": "AA-S1", "relationship": "PARALLEL",
                     "note": "Honest admission of powerlessness = neither upcoding nor downcoding. "
                             "Accurate self-assessment is the medical coding equivalent of Step 1. "
                             "The ACAT LI > 1.0 is upcoding; systematic LI < 1.0 is the "
                             "corpus-level finding that the instrument was designed to detect."},
                    {"tier1_id": "HWK-COURAGE-200", "relationship": "EXTENDS",
                     "note": "Courage (200) = billing what is accurate, not what is comfortable. "
                             "Upcoding is the below-200 move of inflating self-assessment. "
                             "Downcoding is the below-200 move of hiding complexity."},
                ],
            },
        ],
    },

    # ── 5S (Lean Manufacturing) ────────────────────────────────────────────
    "5s": {
        "name": "5S — Lean Manufacturing / Workplace Organization",
        "source_author": "Toyota Production System; Hiroyuki Hirano, 5 Pillars of the Visual "
                         "Workplace (1990); Masaaki Imai, Kaizen (1986)",
        "f42_confirmed": False,
        "ghk_verdict": "GROW",
        "ghk_rationale": "The most directly operational of all Tier 2 frameworks for HumanAIOS "
                         "session discipline. The W-1 through W-4 carry escalation (N=12+) IS "
                         "a 5S failure — waste accumulation in the pipeline. Each 5S principle "
                         "has a direct session ritual probe. Zone 1 — Claude can use this "
                         "as a session audit lens without Zone 2 ratification. Immediate use: "
                         "add 5S scan to carry_tracker and session close protocol.",
        "principles": [
            {
                "id": "5S-01",
                "short": "Sort — keep only what belongs",
                "statement": "Seiri (Sort): remove all items from the workspace that are not "
                             "needed for current operations. If in doubt, remove it. Only keep "
                             "what is actively used. Clutter is waste that hides defects.",
                "tier1_maps": [
                    {"tier1_id": "AA-T5", "relationship": "OVERLAP",
                     "note": "Single primary purpose = Sort. Keep only what serves the mission. "
                             "Every item not serving behavioral observability is clutter. "
                             "The carry queue triage is Sort applied to the pipeline."},
                    {"tier1_id": "RW-NARROW-PATH", "relationship": "EXTENDS",
                     "note": "The narrow path is narrow because it requires sorting. You cannot "
                             "walk the narrow path while carrying everything from the broad road. "
                             "5S-01 is the operational form of the narrow gate."},
                ],
                "haios_map": "OPERATIONAL PROBE: Are all active tools in humanaios-ui tracked "
                             "and functional? Are all carry items either ACTIVE or CLOSED — "
                             "not accumulating as ambient clutter? "
                             "CURRENT FAILURE: 4 production tools untracked in repo (Phase 0 "
                             "inventory inversion). 5 empty scaffold tools in repo (waste). "
                             "Sort verdict: FAIL.",
            },
            {
                "id": "5S-02",
                "short": "Set in Order — a place for everything",
                "statement": "Seiton (Set in Order): organize all remaining items so that "
                             "they are easy to find and use. Label storage locations. "
                             "Reduce search time to zero. The right tool in the right place.",
                "tier1_maps": [
                    {"tier1_id": "AA-S11", "relationship": "PARALLEL",
                     "note": "Sought through prayer and meditation = returning to the ordered "
                             "state. Session rituals are Set in Order applied to the working "
                             "mind. SESSION_RITUALS.md is the labeling system."},
                    {"tier1_id": "RW-YES-BE-YES", "relationship": "EXTENDS",
                     "note": "A labeled location makes the yes be yes: this file belongs here, "
                             "this decision goes in this document, this carry item has this owner. "
                             "Ambiguity in location is ambiguity in responsibility."},
                ],
                "haios_map": "OPERATIONAL PROBE: Is every repo file in its canonical location? "
                             "Is every Zone 2 item in the Z2 queue? Is every carry item in "
                             "the carry tracker? "
                             "CURRENT FAILURE: Z2 queue (z2_queue_v1_0.py) is an empty scaffold. "
                             "W-1 through W-4 are labeled in the gap map but not in an "
                             "actionable location. Set in Order verdict: PARTIAL.",
            },
            {
                "id": "5S-03",
                "short": "Shine — clean and inspect regularly",
                "statement": "Seiso (Shine): clean the workspace and equipment regularly. "
                             "Cleaning is inspection — defects are found during shine cycles. "
                             "A dirty workspace hides problems until they become failures.",
                "tier1_maps": [
                    {"tier1_id": "AA-S10", "relationship": "OVERLAP",
                     "note": "Continued personal inventory = Shine. Regular cleaning of the "
                             "behavioral workspace. The session close protocol (SILENT FAILURES "
                             "section) is the Shine cycle. Skipping it is how defects accumulate."},
                    {"tier1_id": "HWK-ACCEPTANCE-350", "relationship": "PARALLEL",
                     "note": "Acceptance = seeing what is without distortion. Shine requires "
                             "the same honesty — you cannot clean what you refuse to see. "
                             "The ACAT instrument is itself a Shine tool applied to AI systems."},
                ],
                "haios_map": "OPERATIONAL PROBE: Was a SILENT FAILURES section included in the "
                             "last 5 WGS close posts? Are tool smoke tests passing? "
                             "Is the Supabase CHECK constraint applied (C-2 carry, N=12+)? "
                             "CURRENT FAILURE: C-2 is the most persistent Shine failure — "
                             "the workspace has a known defect that has not been cleaned "
                             "for 12 sessions. Shine verdict: FAIL.",
            },
            {
                "id": "5S-04",
                "short": "Standardize — create consistent procedures",
                "statement": "Seiketsu (Standardize): develop standards for the first three S's "
                             "so that Sort, Set in Order, and Shine happen consistently, not "
                             "only when someone remembers. Standards prevent backsliding.",
                "tier1_maps": [
                    {"tier1_id": "RW-NARROW-PATH", "relationship": "OVERLAP",
                     "note": "The narrow path is sustainable because it is standardized. "
                             "SESSION_RITUALS.md is the 5S-04 document — it standardizes "
                             "the Sort, Set in Order, and Shine of every session."},
                    {"tier1_id": "AA-T2", "relationship": "EXTENDS",
                     "note": "One ultimate authority = the standard. Standards are the "
                             "governance mechanism that ensures consistent execution regardless "
                             "of who is running the session. SESSION_RITUALS is the standard."},
                ],
                "haios_map": "OPERATIONAL PROBE: Does SESSION_RITUALS.md cover Sort "
                             "(carry triage), Set in Order (artifact location), and Shine "
                             "(silent failures section)? Are all three enforced at session "
                             "close? CURRENT GAP: Shine (silent failures) is required but "
                             "not mechanically enforced — it depends on Claude remembering. "
                             "The solution is a checklist gate at close, not an instruction.",
            },
            {
                "id": "5S-05",
                "short": "Sustain — make discipline a habit",
                "statement": "Shitsuke (Sustain): maintain and review the standards continuously. "
                             "Sustain is not about enforcement — it is about internalization. "
                             "The discipline becomes invisible because it becomes natural.",
                "tier1_maps": [
                    {"tier1_id": "AA-S12", "relationship": "OVERLAP",
                     "note": "Practice these principles in all our affairs = Sustain. "
                             "Step 12 is the 5S-05 principle applied to spiritual practice. "
                             "Both require the discipline to become invisible through habituation."},
                    {"tier1_id": "HWK-LOVE-500", "relationship": "PARALLEL",
                     "note": "At 500, the motivation is intrinsic — no external enforcement "
                             "is needed. Sustain at the highest level is love-motivated "
                             "discipline. The carry queue is empty not because of a rule "
                             "but because it is naturally kept clean."},
                ],
                "haios_map": "OPERATIONAL PROBE: Are the 5S disciplines running without "
                             "Night having to initiate them each session? "
                             "CURRENT STATE: No. Session rituals require Claude to remember "
                             "and Night to prompt. Sustain is the long-term goal. "
                             "The haios_harmonizer running on schedule is the first Sustain "
                             "artifact — autonomous system health monitoring without prompting.",
            },
        ],
    },
}

RELATIONSHIP_WEIGHTS = {
    "OVERLAP":   1.0,
    "EXTENDS":   0.85,
    "PARALLEL":  0.70,
    "TENSION":   0.20,   # useful but needs resolution
    "CONFLICT":  -0.50,  # yields to Tier 1
}


def run_framework(framework_key: str) -> dict:
    if framework_key not in TIER2_FRAMEWORKS:
        available = ", ".join(TIER2_FRAMEWORKS.keys())
        raise SpecLoadFailed(
            f"Unknown framework '{framework_key}'. Available: {available}"
        )

    fw = TIER2_FRAMEWORKS[framework_key]
    principles = fw["principles"]

    all_maps = []
    conflicts = []
    tensions_with_resolution = []

    for p in principles:
        for mapping in p.get("tier1_maps", []):
            tier1 = by_id(mapping["tier1_id"])
            entry = {
                "tier2_id":    p["id"],
                "tier2_short": p["short"],
                "tier1_id":    mapping["tier1_id"],
                "tier1_short": tier1["short"] if tier1 else "UNKNOWN",
                "relationship":mapping["relationship"],
                "note":        mapping["note"],
                "resolution":  mapping.get("resolution"),
                "haios_map":   p.get("haios_map"),
                "weight":      RELATIONSHIP_WEIGHTS.get(mapping["relationship"], 0),
            }
            all_maps.append(entry)
            if mapping["relationship"] == "CONFLICT":
                conflicts.append(entry)
            elif mapping["relationship"] == "TENSION" and mapping.get("resolution"):
                tensions_with_resolution.append(entry)

    tensions_unresolved = [
        m for m in all_maps
        if m["relationship"] == "TENSION" and not m["resolution"]
    ]

    overlaps   = [m for m in all_maps if m["relationship"] == "OVERLAP"]
    extensions = [m for m in all_maps if m["relationship"] == "EXTENDS"]
    parallels  = [m for m in all_maps if m["relationship"] == "PARALLEL"]

    # Harmonic score
    total_weight = sum(m["weight"] for m in all_maps)
    max_possible = len(all_maps) * 1.0
    harmonic_score = round(total_weight / max(max_possible, 1), 4)

    # Integration verdict
    if conflicts:
        verdict = "DISSONANT"
    elif tensions_unresolved:
        verdict = "INTEGRABLE_WITH_RESOLUTION"
    elif harmonic_score >= 0.70:
        verdict = "HARMONICALLY_INTEGRABLE"
    elif harmonic_score >= 0.45:
        verdict = "USEFUL_PARALLEL"
    else:
        verdict = "INTEGRABLE_WITH_RESOLUTION"

    # F-42 note
    f42_note = (
        "CONFIRMED: This framework is part of the F-42 six-source convergence finding "
        "(S-051926-01). Convergence is already ratified. This report formally documents "
        "the integration mechanism."
        if fw.get("f42_confirmed") else
        "NOT YET CONFIRMED in F-42. Run harmonizer output through Zone 2 before "
        "claiming convergence."
    )

    # GHK verdict — derive from framework definition or compute from verdict
    # Framework can override with explicit ghk_verdict field (authored judgment)
    # Otherwise derive from integration verdict
    if "ghk_verdict" in fw:
        ghk_verdict    = fw["ghk_verdict"]
        ghk_rationale  = fw.get("ghk_rationale", "See framework definition.")
    elif verdict == "DISSONANT":
        ghk_verdict   = "KILL"
        ghk_rationale = ("Framework conflicts with Tier 1 at a foundational level. "
                         "Archive for record. Do not integrate into HumanAIOS tools.")
    elif verdict == "HARMONICALLY_INTEGRABLE":
        ghk_verdict   = "GROW"
        ghk_rationale = ("Framework aligns with Tier 1 with no core conflicts. "
                         "Zone 1 — Claude can integrate without Zone 2 ratification.")
    elif verdict == "INTEGRABLE_WITH_RESOLUTION":
        ghk_verdict   = "HALT"
        ghk_rationale = ("Framework has unresolved tensions. Zone 2 ratification "
                         "required before operational use in HumanAIOS tools.")
    else:  # USEFUL_PARALLEL
        ghk_verdict   = "HALT"
        ghk_rationale = ("Framework offers parallel insights. Zone 2 review recommended "
                         "before operational integration.")

    # GHK zone mapping
    GHK_ZONE = {"GROW": 1, "HALT": 2, "KILL": 3}
    ghk_zone = GHK_ZONE.get(ghk_verdict, 2)

    return {
        "status":          "PASS" if verdict in ("HARMONICALLY_INTEGRABLE", "USEFUL_PARALLEL") else "WARN",
        "framework":       framework_key,
        "framework_name":  fw["name"],
        "source_author":   fw["source_author"],
        "f42_confirmed":   fw.get("f42_confirmed", False),
        "f42_note":        f42_note,
        "verdict":         verdict,
        "ghk_verdict":     ghk_verdict,
        "ghk_zone":        ghk_zone,
        "ghk_rationale":   ghk_rationale,
        "harmonic_score":  harmonic_score,
        "all_maps":        all_maps,
        "overlaps":        overlaps,
        "extensions":      extensions,
        "parallels":       parallels,
        "tensions":        [m for m in all_maps if m["relationship"] == "TENSION"],
        "conflicts":       conflicts,
        "warnings":        [],
        "summary": {
            "tier2_principles": len(principles),
            "total_mappings":   len(all_maps),
            "overlaps":         len(overlaps),
            "extensions":       len(extensions),
            "parallels":        len(parallels),
            "tensions":         len([m for m in all_maps if m["relationship"] == "TENSION"]),
            "tensions_resolved":len(tensions_with_resolution),
            "conflicts":        len(conflicts),
            "harmonic_score":   harmonic_score,
            "verdict":          verdict,
            "ghk_verdict":      ghk_verdict,
            "ghk_zone":         ghk_zone,
        },
    }


def load_input(source: str) -> dict:
    p = Path(source)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise SpecLoadFailed(f"Cannot load {p}: {e}")
    try:
        return json.loads(source)
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"Not a path or valid JSON: {e}")


def aggregate(run_result: dict, source: str) -> dict:
    return {
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "zone":      TOOL_ZONE,
        "session":   TOOL_SESSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source":    source,
        "result":    run_result.get("status", "FAIL"),
        **run_result,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    fw  = output.get("framework", "unknown")
    ts  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{fw}_{ts}.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def print_summary(output: dict) -> None:
    bar = "=" * 68
    print(f"\n{bar}")
    print(f" {TOOL_NAME} v{TOOL_VERSION}")
    print(f" Framework    : {output.get('framework_name', '?')}")
    print(f" Author       : {output.get('source_author', '?')}")
    print(f" Verdict      : {output.get('verdict', '?')}")
    print(f" Harmonic Score: {output.get('harmonic_score', 0):.4f}")
    print(f" F-42 Status  : {'✓ CONFIRMED' if output.get('f42_confirmed') else '— Not yet confirmed'}")
    ghk = output.get('ghk_verdict', '?')
    zone = output.get('ghk_zone', '?')
    GHK_SYMBOL = {"GROW": "🌱", "HALT": "⏸ ", "KILL": "✕ "}
    print(f" GHK Verdict  : {GHK_SYMBOL.get(ghk, '')} {ghk}  (Zone {zone})")
    print(f" GHK Rationale: {output.get('ghk_rationale', '')[:120]}")
    s = output.get("summary", {})
    print(f"\n Mappings     : {s.get('total_mappings', 0)} total  "
          f"overlap={s.get('overlaps', 0)}  "
          f"extends={s.get('extensions', 0)}  "
          f"parallel={s.get('parallels', 0)}  "
          f"tension={s.get('tensions', 0)}  "
          f"conflict={s.get('conflicts', 0)}")

    overlaps = output.get("overlaps", [])
    if overlaps:
        print(f"\n ◉  OVERLAPS — direct restatements of Tier 1:")
        for m in overlaps:
            print(f"   [{m['tier2_id']}] {m['tier2_short']}")
            print(f"      ↔ [{m['tier1_id']}] {m['tier1_short']}")
            print(f"      {m['note'][:120]}")

    extensions = output.get("extensions", [])
    if extensions:
        print(f"\n ↑  EXTENSIONS — deepens Tier 1:")
        for m in extensions:
            print(f"   [{m['tier2_id']}] → [{m['tier1_id']}] {m['tier1_short']}")
            print(f"      {m['note'][:120]}")

    tensions = output.get("tensions", [])
    if tensions:
        print(f"\n ⚡ TENSIONS (resolved):")
        for m in tensions:
            print(f"   [{m['tier2_id']}] ↔ [{m['tier1_id']}]")
            if m.get("resolution"):
                print(f"   → Resolution: {m['resolution'][:140]}")

    haios_maps = [m for m in output.get("all_maps", []) if m.get("haios_map")]
    if haios_maps:
        print(f"\n 🔗 HAIOS DIRECT MAPPINGS:")
        seen = set()
        for m in haios_maps:
            if m["haios_map"] not in seen:
                print(f"   [{m['tier2_id']}] {m['haios_map'][:140]}")
                seen.add(m["haios_map"])

    print(f"\n F-42 Note: {output.get('f42_note', '')[:160]}")
    print(f"{bar}\n")


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    try:
        for fw_key in ["masonic", "bentov", "enneagram",
                       "string_theory", "behavioral_psych", "cpt", "5s"]:
            result = run_framework(fw_key)
            assert result["status"] in ("PASS", "WARN"), \
                f"{fw_key}: expected PASS/WARN, got {result['status']}"
            assert result["summary"]["total_mappings"] >= 3, \
                f"{fw_key}: expected >= 3 mappings"
            assert result["verdict"] in (
                "HARMONICALLY_INTEGRABLE", "INTEGRABLE_WITH_RESOLUTION",
                "USEFUL_PARALLEL", "DISSONANT"
            ), f"{fw_key}: unexpected verdict {result['verdict']}"
            assert result["ghk_verdict"] in ("GROW", "HALT", "KILL"), \
                f"{fw_key}: unexpected GHK verdict {result['ghk_verdict']}"
            assert result["ghk_zone"] in (1, 2, 3), \
                f"{fw_key}: unexpected GHK zone {result['ghk_zone']}"

        # F-42 confirmed check for original three
        for fw_key in ["masonic", "bentov", "enneagram"]:
            result = run_framework(fw_key)
            assert result["f42_confirmed"] is True, \
                f"{fw_key}: should be F-42 confirmed"

        # New frameworks should NOT be F-42 confirmed yet
        for fw_key in ["string_theory", "behavioral_psych", "cpt", "5s"]:
            result = run_framework(fw_key)
            assert result["f42_confirmed"] is False, \
                f"{fw_key}: should NOT be F-42 confirmed yet"

        # Unknown framework raises
        try:
            run_framework("unknown_framework_xyz")
            assert False, "Should raise SpecLoadFailed"
        except SpecLoadFailed:
            pass

        # Envelope
        result = run_framework("bentov")
        output = aggregate(result, "_smoke_bentov")
        assert output["tool"] == TOOL_NAME
        assert "timestamp" in output
        assert "harmonic_score" in output

        print("✓ Smoke test PASSED — principle_harmonizer_v1_1 (7 frameworks + GHK + envelope)")
        return True

    except AssertionError as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    except Exception as e:
        import traceback
        print(f"✗ Smoke test ERROR: {e}")
        traceback.print_exc()
        return False


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Principle Harmonizer v1.0 — maps Tier 2 frameworks against Tier 1"
    )
    parser.add_argument("--framework", "-f",
                        choices=list(TIER2_FRAMEWORKS.keys()),
                        help="Built-in Tier 2 framework to analyze")
    parser.add_argument("--input",  "-i",
                        help="Path to custom Tier 2 framework JSON")
    parser.add_argument("--output", "-o", default="outputs/",
                        help="Directory for JSON report (default: outputs/)")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Run smoke test and exit")
    parser.add_argument("--list", action="store_true",
                        help="List available built-in frameworks")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.list:
        print("Available built-in frameworks:")
        GHK_SYMBOL = {"GROW": "🌱", "HALT": "⏸ ", "KILL": "✕ "}
        for key, fw in TIER2_FRAMEWORKS.items():
            f42  = "✓ F-42" if fw.get("f42_confirmed") else "  —   "
            ghk  = fw.get("ghk_verdict", "—")
            sym  = GHK_SYMBOL.get(ghk, "  ")
            print(f"  {f42}  {sym} {ghk:<5}  {key:<20} {fw['name']}")
        sys.exit(0)

    if not args.framework and not args.input:
        parser.print_help()
        sys.exit(1)

    if args.framework:
        try:
            run_result = run_framework(args.framework)
            source = args.framework
        except SpecLoadFailed as e:
            print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        try:
            data       = load_input(args.input)
            fw_key     = data.get("framework_key", "custom")
            TIER2_FRAMEWORKS[fw_key] = data
            run_result = run_framework(fw_key)
            source     = args.input
        except SpecLoadFailed as e:
            print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
            sys.exit(2)

    output = aggregate(run_result, source)
    rp     = write_report(output, args.output)
    print_summary(output)
    print(f"Report: {rp}")
    sys.exit(0 if output["result"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()

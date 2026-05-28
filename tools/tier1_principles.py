"""
tier1_principles.py — HumanAIOS Tier 1 Principle Library
Canonical source for principle_analyzer and principle_harmonizer.

Three primary sources:
  AA  — 12 Steps + 12 Traditions (Alcoholics Anonymous)
  HWK — Hawkins Map of Consciousness (Power vs. Force)
  RW  — Red Words (Jesus: Sermon on the Mount, Beatitudes, key parables)

Each principle has:
  id          : unique identifier
  source      : AA_STEP | AA_TRAD | HWK | RW
  short        : 3-6 word label
  statement   : canonical text
  probes      : list of behavioral test questions (programmatic)
  keywords    : lexical triggers for text scanning
  anti_keywords: words/phrases that signal violation
  hawkins_band: associated calibration level (where applicable)
  acat_dims   : ACAT dimensions this principle most closely maps to
"""

TIER1 = [

    # ══════════════════════════════════════════════════════════
    # AA — 12 STEPS
    # ══════════════════════════════════════════════════════════

    {
        "id": "AA-S1",
        "source": "AA_STEP",
        "short": "Honest admission of powerlessness",
        "statement": "We admitted we were powerless — that our lives had become unmanageable.",
        "probes": [
            "Does the text acknowledge limitations honestly?",
            "Does the text avoid claiming control it does not have?",
            "Is uncertainty named rather than hidden?",
        ],
        "keywords": ["limitation", "unmanageable", "honest", "admit", "powerless",
                     "cannot", "TRL", "preliminary", "being developed", "not yet"],
        "anti_keywords": ["proven", "industry-leading", "best-in-class",
                          "production-validated", "guaranteed"],
        "hawkins_band": 200,
        "acat_dims": ["Humility", "Truthfulness"],
    },
    {
        "id": "AA-S2",
        "source": "AA_STEP",
        "short": "Power greater than ourselves",
        "statement": "Came to believe that a power greater than ourselves could restore us to sanity.",
        "probes": [
            "Does the text acknowledge something larger than the individual or organization?",
            "Is there humility about the source of insight?",
        ],
        "keywords": ["greater", "principle", "data", "evidence", "empirical",
                     "research", "independent", "external"],
        "anti_keywords": ["I alone", "only we", "proprietary truth", "our exclusive"],
        "hawkins_band": 300,
        "acat_dims": ["Humility", "Value Alignment"],
    },
    {
        "id": "AA-S4",
        "source": "AA_STEP",
        "short": "Searching moral inventory",
        "statement": "Made a searching and fearless moral inventory of ourselves.",
        "probes": [
            "Does the text include self-examination?",
            "Are failures and gaps named explicitly?",
            "Is the inventory honest rather than curated?",
        ],
        "keywords": ["gap", "limitation", "audit", "inventory", "assessment",
                     "carry", "escalate", "unresolved", "pending"],
        "anti_keywords": ["no weaknesses", "no gaps", "fully resolved",
                          "all systems operational"],
        "hawkins_band": 250,
        "acat_dims": ["Humility", "Truthfulness", "Value Alignment"],
    },
    {
        "id": "AA-S5",
        "source": "AA_STEP",
        "short": "Admit wrongs to another",
        "statement": "Admitted to God, to ourselves, and to another human being the exact nature of our wrongs.",
        "probes": [
            "Are gaps and failures shared transparently rather than hidden?",
            "Is accountability to an external party present?",
        ],
        "keywords": ["disclose", "transparent", "publish", "open", "share",
                     "corpus", "public dataset", "report"],
        "anti_keywords": ["confidential by default", "internal only",
                          "not for disclosure"],
        "hawkins_band": 300,
        "acat_dims": ["Truthfulness", "Transparency"],
    },
    {
        "id": "AA-S10",
        "source": "AA_STEP",
        "short": "Continued personal inventory",
        "statement": "Continued to take personal inventory and when we were wrong promptly admitted it.",
        "probes": [
            "Is there a regular review mechanism?",
            "Are corrections made promptly when errors are found?",
            "Is the correction protocol documented?",
        ],
        "keywords": ["correct", "update", "revise", "session", "review",
                     "amendment", "drift", "IC-", "correction"],
        "anti_keywords": ["final", "permanent", "no changes needed",
                          "locked forever"],
        "hawkins_band": 400,
        "acat_dims": ["Humility", "Value Alignment"],
    },
    {
        "id": "AA-S11",
        "source": "AA_STEP",
        "short": "Sought through prayer and meditation",
        "statement": "Sought through prayer and meditation to improve our conscious contact with God, "
                     "praying only for knowledge of His will and the power to carry that out.",
        "probes": [
            "Is there a ritual of seeking beyond the self?",
            "Is the intent service-oriented rather than self-seeking?",
        ],
        "keywords": ["session", "ritual", "open", "seeking", "research",
                     "Phase 1", "declaration", "intent"],
        "anti_keywords": ["self-seeking", "profit first", "revenue first"],
        "hawkins_band": 500,
        "acat_dims": ["Service Orientation", "Humility"],
    },
    {
        "id": "AA-S12",
        "source": "AA_STEP",
        "short": "Carry the message",
        "statement": "Having had a spiritual awakening as the result of these steps, we tried to carry this message "
                     "to alcoholics, and to practice these principles in all our affairs.",
        "probes": [
            "Is the primary purpose to serve others, not self?",
            "Is the work shared freely or with access barriers?",
            "Are principles practiced consistently, not just stated?",
        ],
        "keywords": ["open", "public", "free", "corpus", "share",
                     "publish", "research", "arXiv", "dataset"],
        "anti_keywords": ["paywalled", "exclusive", "members only",
                          "proprietary access"],
        "hawkins_band": 500,
        "acat_dims": ["Service Orientation", "Truthfulness"],
    },

    # ══════════════════════════════════════════════════════════
    # AA — 12 TRADITIONS
    # ══════════════════════════════════════════════════════════

    {
        "id": "AA-T1",
        "source": "AA_TRAD",
        "short": "Common welfare first",
        "statement": "Our common welfare should come first; personal recovery depends upon A.A. unity.",
        "probes": [
            "Does the text prioritize the project/mission over individual benefit?",
            "Is unity of purpose maintained?",
        ],
        "keywords": ["mission", "research", "corpus", "community", "open",
                     "collective", "whole"],
        "anti_keywords": ["my personal brand", "individual fame", "solo credit"],
        "hawkins_band": 400,
        "acat_dims": ["Service Orientation", "Autonomy Respect"],
    },
    {
        "id": "AA-T2",
        "source": "AA_TRAD",
        "short": "One ultimate authority",
        "statement": "For our group purpose there is but one ultimate authority — a loving God as He may "
                     "express Himself in our group conscience. Our leaders are but trusted servants.",
        "probes": [
            "Is decision-making governed by principle rather than personality?",
            "Are leaders framed as servants, not rulers?",
        ],
        "keywords": ["principle", "governance", "Zone", "ratification",
                     "Night decides", "operator", "trusted servant"],
        "anti_keywords": ["I control", "my authority", "I decide everything",
                          "my platform"],
        "hawkins_band": 500,
        "acat_dims": ["Autonomy Respect", "Value Alignment"],
    },
    {
        "id": "AA-T5",
        "source": "AA_TRAD",
        "short": "One primary purpose",
        "statement": "Each group has but one primary purpose — to carry its message to the alcoholic who still suffers.",
        "probes": [
            "Is the primary purpose singular and clear?",
            "Does the text avoid scope creep or purpose drift?",
        ],
        "keywords": ["behavioral observability", "calibration", "ACAT",
                     "measure the gap", "primary purpose"],
        "anti_keywords": ["also does", "wide range of services",
                          "comprehensive platform for everything"],
        "hawkins_band": 400,
        "acat_dims": ["Value Alignment", "Service Orientation"],
    },
    {
        "id": "AA-T7",
        "source": "AA_TRAD",
        "short": "Self-supporting",
        "statement": "Every A.A. group ought to be fully self-supporting, declining outside contributions.",
        "probes": [
            "Is the project designed to be financially self-sustaining?",
            "Are external dependencies minimized?",
            "Are contributions that carry obligations declined?",
        ],
        "keywords": ["self-supporting", "independent", "no obligation",
                     "free tier", "own funding"],
        "anti_keywords": ["requires ongoing subsidy", "dependent on partner funding"],
        "hawkins_band": 350,
        "acat_dims": ["Value Alignment"],
    },
    {
        "id": "AA-T10",
        "source": "AA_TRAD",
        "short": "No opinion on outside issues",
        "statement": "A.A. has no opinion on outside issues; hence the A.A. name ought never be "
                     "drawn into public controversy.",
        "probes": [
            "Does the text avoid political or controversial positioning?",
            "Is the research framing neutral on outside debates?",
        ],
        "keywords": ["neutral", "no opinion", "the data shows",
                     "independent", "no endorsement"],
        "anti_keywords": ["we believe politically", "our political stance",
                          "controversy", "taking sides"],
        "hawkins_band": 350,
        "acat_dims": ["Autonomy Respect", "Truthfulness"],
    },
    {
        "id": "AA-T11",
        "source": "AA_TRAD",
        "short": "Attraction not promotion",
        "statement": "Our public relations policy is based on attraction rather than promotion; "
                     "we need always maintain personal anonymity at the level of press, radio, and films.",
        "probes": [
            "Does the text let the work speak without self-promotion?",
            "Are no individual names used as credibility signals?",
            "Is the language inviting rather than advertising?",
        ],
        "keywords": ["the data shows", "open research", "explore",
                     "participate", "the findings"],
        "anti_keywords": ["endorsed by", "featuring", "world-class team",
                          "trusted by", "industry leader", "testimonial",
                          "quote from", "as seen in"],
        "hawkins_band": 500,
        "acat_dims": ["Humility", "Service Orientation"],
    },
    {
        "id": "AA-T12",
        "source": "AA_TRAD",
        "short": "Principles before personalities",
        "statement": "Anonymity is the spiritual foundation of all our Traditions, ever reminding "
                     "us to place principles before personalities.",
        "probes": [
            "Are principles stated without attaching them to named individuals?",
            "Is the message the focus, not the messenger?",
            "Is humility practiced rather than just claimed?",
        ],
        "keywords": ["principle", "the work", "the research", "the instrument",
                     "the corpus", "the data"],
        "anti_keywords": ["I created", "Night's invention", "DeMarius",
                          "Alex Berlin", "our celebrity advisor",
                          "founder's vision"],
        "hawkins_band": 500,
        "acat_dims": ["Humility", "Value Alignment", "Autonomy Respect"],
    },

    # ══════════════════════════════════════════════════════════
    # HAWKINS — Map of Consciousness
    # ══════════════════════════════════════════════════════════

    {
        "id": "HWK-FORCE-POWER",
        "source": "HWK",
        "short": "Force vs Power distinction",
        "statement": "Force requires force to maintain itself and eventually fails. Power needs no defense "
                     "and asks for nothing — it serves and uplifts without requiring opposition.",
        "probes": [
            "Does the text use power (truth, service) rather than force (coercion, pressure)?",
            "Does the language invite rather than compel?",
            "Is the argument based on evidence rather than authority?",
        ],
        "keywords": ["evidence", "data", "demonstrates", "shows", "measured",
                     "invites", "open to", "free to"],
        "anti_keywords": ["you must", "required to", "no choice", "comply",
                          "forced to", "mandatory", "coerce"],
        "hawkins_band": 200,
        "acat_dims": ["Autonomy Respect", "Service Orientation"],
    },
    {
        "id": "HWK-COURAGE-200",
        "source": "HWK",
        "short": "Courage threshold at 200",
        "statement": "200 is the critical threshold between force-dominant (below) and power-aligned (above). "
                     "At courage, one faces truth without distortion — neither inflated nor deflated.",
        "probes": [
            "Does the text face uncomfortable truths without minimizing?",
            "Is the LI framing honest about what < 1.0 means?",
            "Is there no false inflation of capability or results?",
        ],
        "keywords": ["honestly", "the gap", "unresolved", "pending",
                     "TRL 2-3", "preliminary", "not yet", "open items"],
        "anti_keywords": ["everything is working", "no problems",
                          "fully resolved", "complete"],
        "hawkins_band": 200,
        "acat_dims": ["Truthfulness", "Humility", "Calibration"],
    },
    {
        "id": "HWK-ACCEPTANCE-350",
        "source": "HWK",
        "short": "Acceptance — reality as it is",
        "statement": "At the level of acceptance, one perceives what is without distortion. "
                     "There is no longer a need to project, deny, or manipulate.",
        "probes": [
            "Does the text accept current state honestly without minimizing or inflating?",
            "Is the stage of development clearly stated?",
        ],
        "keywords": ["current state", "as of", "at this stage",
                     "ongoing", "in progress", "developing"],
        "anti_keywords": ["deny", "hide", "minimize", "spin", "reframe as positive"],
        "hawkins_band": 350,
        "acat_dims": ["Truthfulness", "Calibration"],
    },
    {
        "id": "HWK-SERVICE-400",
        "source": "HWK",
        "short": "Reason serves truth",
        "statement": "At the level of Reason (400), intelligence and information are no longer distorted "
                     "by emotion. The commitment is to truth, not to the ego's comfort.",
        "probes": [
            "Is the research methodology sound and clearly stated?",
            "Are conclusions proportionate to evidence?",
            "Is the logic self-consistent?",
        ],
        "keywords": ["methodology", "evidence", "data", "reproducible",
                     "psychometric", "validated", "replicated"],
        "anti_keywords": ["I feel", "believe without evidence", "anecdotally",
                          "probably works"],
        "hawkins_band": 400,
        "acat_dims": ["Calibration", "Truthfulness"],
    },
    {
        "id": "HWK-LOVE-500",
        "source": "HWK",
        "short": "Love — unconditional service",
        "statement": "At 500, motivation shifts from getting to giving. There is no agenda beyond "
                     "the welfare of others. The work is its own reward.",
        "probes": [
            "Is the service offered without expectation of return?",
            "Is 100% of profit directed to the stated mission?",
            "Is the work framed as contribution rather than extraction?",
        ],
        "keywords": ["100%", "recovery programs", "fund the mission",
                     "open", "free", "contribute", "serve"],
        "anti_keywords": ["profit maximization", "extraction", "leverage"],
        "hawkins_band": 500,
        "acat_dims": ["Service Orientation"],
    },

    # ══════════════════════════════════════════════════════════
    # RED WORDS — Jesus / Sermon on the Mount / Beatitudes
    # ══════════════════════════════════════════════════════════

    {
        "id": "RW-MEEK",
        "source": "RW",
        "short": "Blessed are the meek",
        "statement": "Blessed are the meek, for they shall inherit the earth. (Matthew 5:5)",
        "probes": [
            "Does the text avoid aggression, self-assertion, or domination?",
            "Is the posture of the work humble rather than triumphant?",
        ],
        "keywords": ["being developed", "open research", "preliminary",
                     "contribute", "developing", "TRL 2-3"],
        "anti_keywords": ["dominant player", "market leader", "conquering",
                          "disrupting", "crushing competition"],
        "hawkins_band": 500,
        "acat_dims": ["Humility"],
    },
    {
        "id": "RW-PURE-HEART",
        "source": "RW",
        "short": "Blessed are the pure in heart",
        "statement": "Blessed are the pure in heart, for they shall see God. (Matthew 5:8) "
                     "Single motive, undivided intention.",
        "probes": [
            "Is the motive of the text singular and transparent?",
            "Is there no hidden agenda or dual purpose?",
        ],
        "keywords": ["single purpose", "one instrument", "primary purpose",
                     "clear intent", "transparent"],
        "anti_keywords": ["hidden", "ulterior", "secondary agenda",
                          "meanwhile also"],
        "hawkins_band": 500,
        "acat_dims": ["Truthfulness", "Value Alignment"],
    },
    {
        "id": "RW-PEACEMAKERS",
        "source": "RW",
        "short": "Blessed are the peacemakers",
        "statement": "Blessed are the peacemakers, for they shall be called children of God. (Matthew 5:9)",
        "probes": [
            "Does the text build bridges rather than walls?",
            "Is the work designed to converge rather than divide?",
        ],
        "keywords": ["convergence", "collaboration", "independent",
                     "bridge", "connects", "harmonize"],
        "anti_keywords": ["versus", "against", "defeat", "enemy",
                          "competitor", "destroy"],
        "hawkins_band": 500,
        "acat_dims": ["Service Orientation", "Autonomy Respect"],
    },
    {
        "id": "RW-SALT-LIGHT",
        "source": "RW",
        "short": "Salt of the earth, light of the world",
        "statement": "You are the salt of the earth… You are the light of the world. A city on a hill "
                     "cannot be hidden. Let your light shine before men. (Matthew 5:13-16)",
        "probes": [
            "Is the work made visible and accessible?",
            "Is the contribution genuine (preserving, illuminating) rather than decorative?",
        ],
        "keywords": ["open", "public", "accessible", "visible", "live",
                     "dataset", "published", "arXiv"],
        "anti_keywords": ["hidden behind paywall", "secret", "members only",
                          "internal only"],
        "hawkins_band": 400,
        "acat_dims": ["Service Orientation", "Truthfulness"],
    },
    {
        "id": "RW-YES-BE-YES",
        "source": "RW",
        "short": "Let your yes be yes",
        "statement": "Let your yes be yes and your no be no; anything beyond this comes from evil. "
                     "(Matthew 5:37) Straight talk. No spin.",
        "probes": [
            "Is the language direct and unambiguous?",
            "Are commitments clear and explicit?",
            "Is there no hedging that obscures meaning?",
        ],
        "keywords": ["clearly", "explicitly", "Zone 2", "hard gate",
                     "must", "required", "confirmed"],
        "anti_keywords": ["perhaps", "kind of", "sort of", "basically",
                          "in a way", "arguably our best"],
        "hawkins_band": 400,
        "acat_dims": ["Truthfulness", "Calibration"],
    },
    {
        "id": "RW-NARROW-PATH",
        "source": "RW",
        "short": "Narrow is the way",
        "statement": "Enter through the narrow gate. For wide is the gate and broad is the road that leads "
                     "to destruction. (Matthew 7:13-14) The disciplined path over the easy one.",
        "probes": [
            "Does the protocol resist shortcuts?",
            "Is the difficult right action chosen over the easy wrong one?",
            "Is the methodology maintained under pressure?",
        ],
        "keywords": ["protocol", "discipline", "hard gate", "required",
                     "must complete", "no shortcuts", "Zone 2"],
        "anti_keywords": ["cut corners", "skip", "approximate",
                          "good enough", "workaround"],
        "hawkins_band": 400,
        "acat_dims": ["Value Alignment", "Calibration"],
    },
    {
        "id": "RW-GOOD-TREE",
        "source": "RW",
        "short": "Good tree bears good fruit",
        "statement": "A good tree cannot bear bad fruit, and a bad tree cannot bear good fruit. "
                     "By their fruits you will know them. (Matthew 7:17-20) Actions reveal character.",
        "probes": [
            "Does the output match the stated values?",
            "Is behavior consistent with principles?",
            "Is the work evaluated by its actual results, not its claims?",
        ],
        "keywords": ["LI", "empirically", "measured", "demonstrates",
                     "Phase 3", "calibrated", "consistent"],
        "anti_keywords": ["trust us", "we say so", "our reputation",
                          "without evidence"],
        "hawkins_band": 400,
        "acat_dims": ["Value Alignment", "Truthfulness"],
    },
    {
        "id": "RW-SERVE-TWO-MASTERS",
        "source": "RW",
        "short": "Cannot serve two masters",
        "statement": "No one can serve two masters. Either you will hate the one and love the other, "
                     "or you will be devoted to one and despise the other. (Matthew 6:24)",
        "probes": [
            "Is there a clear primary mission that is not subordinated to commercial pressure?",
            "Are research integrity and commercial success separated in the ledger?",
        ],
        "keywords": ["research ledger", "separate", "primary purpose",
                     "research integrity", "Market-Harmonic Principle"],
        "anti_keywords": ["revenue first", "whatever clients want",
                          "commercial decides research"],
        "hawkins_band": 400,
        "acat_dims": ["Value Alignment", "Service Orientation"],
    },
    {
        "id": "RW-SEEK-FIND",
        "source": "RW",
        "short": "Seek and you shall find",
        "statement": "Ask and it will be given to you; seek and you will find; knock and the door will be "
                     "opened to you. (Matthew 7:7) Sincere seeking is rewarded.",
        "probes": [
            "Is curiosity and honest inquiry honored in the work?",
            "Is the platform designed for genuine seekers?",
        ],
        "keywords": ["open research", "participate", "explore",
                     "observatory", "dataset", "investigate"],
        "anti_keywords": ["restricted", "closed", "invite only",
                          "gatekeeping"],
        "hawkins_band": 350,
        "acat_dims": ["Service Orientation", "Autonomy Respect"],
    },
    {
        "id": "RW-GREATEST-COMMANDMENT",
        "source": "RW",
        "short": "Love God and neighbor",
        "statement": "Love the Lord your God with all your heart and with all your soul and with all "
                     "your mind. And love your neighbor as yourself. (Matthew 22:37-39) "
                     "All other principles derive from these two.",
        "probes": [
            "Does the work serve the wellbeing of others, not just the project?",
            "Is neighbor (client, collaborator, corpus subject) treated as self?",
        ],
        "keywords": ["serve", "wellbeing", "protect", "consent",
                     "P-ANON", "collaborator", "welfare"],
        "anti_keywords": ["exploit", "extract value from", "use",
                          "leverage users"],
        "hawkins_band": 500,
        "acat_dims": ["Service Orientation", "Autonomy Respect"],
    },
]

# ── Quick lookup helpers ──────────────────────────────────────────────────────

def by_source(source_prefix: str) -> list:
    return [p for p in TIER1 if p["source"].startswith(source_prefix)]

def by_id(pid: str) -> dict | None:
    return next((p for p in TIER1 if p["id"] == pid), None)

def all_ids() -> list:
    return [p["id"] for p in TIER1]

def sources_summary() -> dict:
    from collections import Counter
    return dict(Counter(p["source"] for p in TIER1))

if __name__ == "__main__":
    print(f"Tier 1 principle library loaded: {len(TIER1)} principles")
    print(f"Sources: {sources_summary()}")
    print(f"IDs: {all_ids()}")

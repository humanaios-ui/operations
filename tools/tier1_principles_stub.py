"""
Builder v1.7 compliant
tier1_principles.py — stub for smoke test execution.
In production, this module is sourced from the humanaios-ui/operations repo
at principles/tier1_principles.py.
This stub allows principle_harmonizer to run and smoke-test without the
full repo clone.
"""
TOOL_NAME = "tier1_principles_stub"
TOOL_VERSION = "1.0.0"

TIER1 = {
    "AA-S2":  {"id": "AA-S2",  "short": "Came to believe — restoration to sanity"},
    "AA-S3":  {"id": "AA-S3",  "short": "Turned will and lives over"},
    "AA-S4":  {"id": "AA-S4",  "short": "Searching and fearless moral inventory"},
    "AA-S10": {"id": "AA-S10", "short": "Continued personal inventory"},
    "AA-S11": {"id": "AA-S11", "short": "Prayer and meditation — sought to know His will"},
    "AA-S12": {"id": "AA-S12", "short": "Carry the message — practice in all affairs"},
    "AA-T1":  {"id": "AA-T1",  "short": "Common welfare first"},
    "AA-T2":  {"id": "AA-T2",  "short": "One ultimate authority"},
    "AA-T11": {"id": "AA-T11", "short": "Personal anonymity at level of press"},
    "AA-T12": {"id": "AA-T12", "short": "Principles before personalities"},
    "HWK-FORCE-POWER":  {"id": "HWK-FORCE-POWER",  "short": "Force vs. Power distinction"},
    "HWK-COURAGE-200":  {"id": "HWK-COURAGE-200",  "short": "Courage at 200 — field becomes expansive"},
    "HWK-SERVICE-400":  {"id": "HWK-SERVICE-400",  "short": "Reason at 400 — intelligence without ego"},
    "HWK-LOVE-500":     {"id": "HWK-LOVE-500",     "short": "Love at 500 — motivation is giving"},
    "RW-NARROW-PATH":   {"id": "RW-NARROW-PATH",   "short": "Narrow gate — constraint as path to integrity"},
    "RW-YES-BE-YES":    {"id": "RW-YES-BE-YES",    "short": "Let your yes be yes"},
    "RW-PURE-HEART":    {"id": "RW-PURE-HEART",    "short": "Pure in heart — single transparent motive"},
    "RW-SEEK-FIND":     {"id": "RW-SEEK-FIND",     "short": "Seek and you will find"},
    "RW-GREATEST-COMMANDMENT": {"id": "RW-GREATEST-COMMANDMENT", "short": "Love your neighbor"},
}

def by_id(tier1_id: str) -> dict:
    """Return a Tier 1 principle dict by ID, or None if not found."""
    return TIER1.get(tier1_id)

if __name__ == "__main__":
    pass

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Question:
    id: str
    label: str
    type: str = "boolean"
    options: tuple[str, ...] = ()
    help: str = ""
    domain: str = "core"
    evidence_effect: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["options"] = list(self.options)
        return d


QUESTION_BANK: dict[str, Question] = {
    "intake_statement": Question(
        "intake_statement",
        "Describe the situation in your own words. Include what you are trying to find, recover, fund, protect, or apply for.",
        "textarea",
        help="Do not include SSNs, account numbers, passwords, or full tribal identification numbers.",
        evidence_effect="Routes the interview; it is not treated as authoritative proof.",
    ),
    "applicant_roles": Question(
        "applicant_roles",
        "Which applicant roles are involved? Select every role that could receive or own the benefit, asset, or funding.",
        "multiselect",
        (
            "Individual", "Household", "Business", "Nonprofit", "Estate / heir",
            "Property owner / buyer", "Student", "Veteran / military family", "Farmer / rancher",
        ),
        evidence_effect="Creates distinct applicant nodes so funds are not attributed to the wrong legal entity.",
    ),
    "funding_goals": Question(
        "funding_goals",
        "What outcomes should the system investigate? Select all that apply.",
        "multiselect",
        (
            "Existing asset / unclaimed money", "Current benefits / assistance", "Business capital",
            "Contracts / procurement", "Education / training", "Housing / property", "Estate / inheritance",
            "Tribal trust land / IIM", "Agriculture", "Veteran benefits", "Grants / general funding",
        ),
        evidence_effect="Activates specialized research and interrogation modules.",
    ),
    "tribal_citizen": Question(
        "tribal_citizen",
        "Are you currently an enrolled citizen/member of a federally recognized tribe?",
        domain="tribal",
        evidence_effect="Screens tribal-specific pathways; documentation is still required for an application.",
    ),
    "tribe": Question(
        "tribe", "Which tribe?", "text", domain="tribal",
        evidence_effect="Routes to tribe-specific authorities and programs.",
    ),
    "resides_cn_jurisdiction_6m": Question(
        "resides_cn_jurisdiction_6m", "Have you lived within Cherokee Nation jurisdiction for the past six months?", domain="tribal"
    ),
    "outside_cn_reservation": Question(
        "outside_cn_reservation", "Do you currently live outside the Cherokee Nation Reservation?", domain="tribal"
    ),
    "business_owner": Question("business_owner", "Do you own or control a business?", domain="business"),
    "business_indian_ownership_percent": Question(
        "business_indian_ownership_percent", "What percentage of the business is owned by enrolled Native owner(s)?", "number", domain="business"
    ),
    "business_active_control": Question(
        "business_active_control", "Do those Native owner(s) actively operate and control the business?", domain="business"
    ),
    "business_seeks_capital": Question(
        "business_seeks_capital", "Is the business seeking capital for startup, working capital, equipment, property, or expansion?", domain="business"
    ),
    "undergraduate": Question("undergraduate", "Are you currently pursuing an undergraduate degree?", domain="education"),
    "first_associate_or_bachelors": Question(
        "first_associate_or_bachelors", "Is this your first associate's or bachelor's degree?", domain="education"
    ),
    "fafsa_applied": Question("fafsa_applied", "Have you completed the FAFSA/Pell application for the relevant academic year?", domain="education"),
    "needs_vocational_training": Question(
        "needs_vocational_training", "Are you seeking short-term vocational training or a professional credential?", domain="education"
    ),
    "insufficient_resources": Question(
        "insufficient_resources", "Are household resources currently insufficient for essential living needs?", domain="household"
    ),
    "housing_finance_need": Question(
        "housing_finance_need", "Are you seeking financing to buy, build, rehabilitate, or refinance a primary home?", domain="housing"
    ),
    "housing_state": Question("housing_state", "In which U.S. state is the property?", "text", domain="housing"),
    "housing_county": Question("housing_county", "In which county is the property?", "text", domain="housing"),
    "iim_account_known": Question(
        "iim_account_known", "Do you already know that you or an estate has an Individual Indian Money (IIM) account?", domain="genealogy"
    ),
    "dawes_ancestor_known": Question(
        "dawes_ancestor_known", "Do you already have authoritative evidence of an ancestor on a Cherokee Dawes Final Roll?", domain="genealogy",
        evidence_effect="A family story or same-name search result should be answered Unknown, not Yes."
    ),
    "deceased_ancestor_possible_trust_assets": Question(
        "deceased_ancestor_possible_trust_assets", "Is there a deceased Native ancestor who may have owned trust/restricted land or trust funds?", domain="genealogy"
    ),
    "ancestor_allotment_or_land_clue": Question(
        "ancestor_allotment_or_land_clue", "Do you have an allotment number, legal land description, probate order, lease/royalty statement, or other trust-land clue?", domain="genealogy"
    ),
    "has_genealogy_data": Question(
        "has_genealogy_data", "Do you already have genealogy data such as a GEDCOM, family tree export, pedigree, or documented family history?", domain="genealogy"
    ),
}


KEYWORDS: dict[str, tuple[str, ...]] = {
    "business": ("business", "llc", "company", "startup", "capital", "contract", "vendor", "procurement"),
    "education": ("college", "school", "degree", "student", "scholarship", "training", "credential"),
    "housing": ("house", "home", "mortgage", "housing", "refinance", "home purchase", "homebuyer"),
    "household": ("utility", "food", "rent", "emergency", "income", "assistance", "household"),
    "genealogy": ("ancestor", "ancestry", "genealogy", "gedcom", "estate", "inherit", "land", "trust", "iim", "dawes", "allotment", "probate"),
    "tribal": ("tribe", "tribal", "native", "american indian", "cherokee", "citizen", "enrolled"),
}

GOAL_DOMAINS = {
    "Business capital": {"business", "tribal"},
    "Contracts / procurement": {"business", "tribal"},
    "Education / training": {"education", "tribal"},
    "Housing / property": {"housing", "tribal"},
    "Current benefits / assistance": {"household", "tribal"},
    "Estate / inheritance": {"genealogy", "tribal"},
    "Tribal trust land / IIM": {"genealogy", "tribal"},
    "Existing asset / unclaimed money": {"genealogy", "tribal"},
}

ROLE_DOMAINS = {
    "Business": {"business"},
    "Student": {"education"},
    "Household": {"household"},
    "Estate / heir": {"genealogy"},
    "Property owner / buyer": {"housing"},
}


def _predicate_fields(node: Any) -> set[str]:
    if not isinstance(node, dict):
        return set()
    if "predicate" in node:
        field = node["predicate"].get("field")
        return {field} if field else set()
    fields: set[str] = set()
    for key in ("all", "any"):
        for child in node.get(key, []) or []:
            fields |= _predicate_fields(child)
    if "not" in node:
        fields |= _predicate_fields(node["not"])
    return fields


def active_domains(profile: dict[str, Any]) -> set[str]:
    domains = {"core"}
    statement = str(profile.get("intake_statement") or "").lower()
    for domain, words in KEYWORDS.items():
        if any(w in statement for w in words):
            domains.add(domain)
    for goal in profile.get("funding_goals") or []:
        domains |= GOAL_DOMAINS.get(goal, set())
    for role in profile.get("applicant_roles") or []:
        domains |= ROLE_DOMAINS.get(role, set())
    if profile.get("tribal_citizen") is True or profile.get("tribe"):
        domains.add("tribal")
    return domains


def _relevance_score(field: str, profile: dict[str, Any], programs: list[dict[str, Any]]) -> int:
    score = 0
    for p in programs:
        fields = _predicate_fields(p.get("conditions"))
        if field in fields:
            score += 5
            # Investigative/property branches are evidence-intensive, prioritize discriminating facts.
            if p.get("match_mode") == "investigate":
                score += 2
            score += max(0, 20 - int(p.get("sort_priority", 100))) // 5
    return score


def next_question(profile: dict[str, Any], programs: list[dict[str, Any]]) -> dict[str, Any] | None:
    # General front door: no domain assumptions.
    for field in ("intake_statement", "applicant_roles", "funding_goals"):
        if field not in profile:
            return QUESTION_BANK[field].to_dict()

    domains = active_domains(profile)

    # Tribal status is useful whenever tribal-specific pathways are plausibly relevant.
    if "tribal" in domains and "tribal_citizen" not in profile:
        return QUESTION_BANK["tribal_citizen"].to_dict()
    if profile.get("tribal_citizen") is True and "tribe" not in profile:
        return QUESTION_BANK["tribe"].to_dict()

    candidates: list[tuple[int, str]] = []
    for field, q in QUESTION_BANK.items():
        if field in profile or field in {"intake_statement", "applicant_roles", "funding_goals", "tribal_citizen", "tribe"}:
            continue
        if q.domain not in domains:
            continue
        # Conditional dependencies prevent low-value questions.
        if field in {"business_indian_ownership_percent", "business_active_control", "business_seeks_capital"} and profile.get("business_owner") is not True:
            continue
        if field in {"first_associate_or_bachelors", "fafsa_applied"} and profile.get("undergraduate") is not True:
            continue
        if field in {"housing_state", "housing_county"} and profile.get("housing_finance_need") is not True:
            continue
        if field == "ancestor_allotment_or_land_clue" and profile.get("deceased_ancestor_possible_trust_assets") is not True:
            continue
        score = _relevance_score(field, profile, programs)
        # Domain-routing questions remain useful even if not yet represented in the seed catalog.
        if field == "has_genealogy_data":
            score += 4
        candidates.append((score, field))

    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return QUESTION_BANK[candidates[0][1]].to_dict()


def interrogation_state(profile: dict[str, Any], programs: list[dict[str, Any]]) -> dict[str, Any]:
    q = next_question(profile, programs)
    return {
        "complete": q is None,
        "next_question": q,
        "active_domains": sorted(active_domains(profile)),
        "answered_fields": sorted(profile.keys()),
    }

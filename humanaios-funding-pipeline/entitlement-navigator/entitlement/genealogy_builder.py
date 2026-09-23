from __future__ import annotations

from datetime import date
from typing import Any


PERSON_FIELDS = (
    ("name", "What is this person's best-known full name?", "text"),
    ("name_variants", "What other names, maiden names, spellings, or aliases are known?", "list"),
    ("birth_date", "What is known about their birth date? Exact, approximate, or a range is acceptable.", "text"),
    ("birth_place", "What is known about their birth place?", "text"),
    ("death_date", "If deceased, what is known about their death date?", "text"),
    ("death_place", "If deceased, what is known about their death place?", "text"),
    ("father_name", "What is known about their father or paternal parent?", "text"),
    ("mother_name", "What is known about their mother or maternal parent?", "text"),
    ("tribal_or_native_clue", "Is there any tribal, Native, enrollment, allotment, agency, reservation, or Indian Territory clue attached to this person?", "text"),
    ("evidence", "What source supports these facts (certificate, census, obituary, family Bible, tree, story, court record, etc.)?", "text"),
)


def new_draft() -> dict[str, Any]:
    return {"people": [{"key": "P1", "relation": "focus person"}], "relationships": [], "active_person": "P1"}


def _person(draft: dict[str, Any], key: str) -> dict[str, Any]:
    return next(p for p in draft.get("people", []) if p.get("key") == key)


def next_genealogy_question(draft: dict[str, Any]) -> dict[str, Any] | None:
    people = draft.setdefault("people", [])
    if not people:
        draft.update(new_draft())
        people = draft["people"]
    active = draft.get("active_person") or people[-1]["key"]
    person = _person(draft, active)
    for field, label, typ in PERSON_FIELDS:
        if field not in person:
            return {"id": field, "person_key": active, "relation": person.get("relation", "relative"), "label": label, "type": typ}
    # Ask whether to add parents once a person is characterized.
    if "parents_complete" not in person:
        return {
            "id": "parents_complete",
            "person_key": active,
            "relation": person.get("relation", "relative"),
            "label": "Should the interview add this person's parents as separate people so the ancestral chain can continue?",
            "type": "boolean",
        }
    # Continue with any already-created relative that still needs characterization.
    for candidate in people:
        if candidate.get("key") == active:
            continue
        if any(field not in candidate for field, _, _ in PERSON_FIELDS) or "parents_complete" not in candidate:
            draft["active_person"] = candidate["key"]
            return next_genealogy_question(draft)
    return None


def apply_genealogy_answer(draft: dict[str, Any], question: dict[str, Any], answer: Any) -> dict[str, Any]:
    person = _person(draft, question["person_key"])
    person[question["id"]] = answer
    if question["id"] == "parents_complete" and answer is True:
        for role, name_field in (("father", "father_name"), ("mother", "mother_name")):
            name = str(person.get(name_field) or "").strip()
            if not name:
                continue
            key = f"P{len(draft['people']) + 1}"
            draft["people"].append({"key": key, "relation": f"{role} of {person.get('name') or person['key']}", "name": name})
            draft["relationships"].append({"child": person["key"], "parent": key, "role": role})
        # Depth-first: continue on the first newly added parent missing facts.
        for p in reversed(draft["people"]):
            if p["key"] != person["key"] and "birth_date" not in p:
                draft["active_person"] = p["key"]
                break
    return draft


def _gedcom_date(value: str) -> str:
    return str(value or "").strip()


def draft_to_gedcom(draft: dict[str, Any]) -> str:
    """Export a conservative GEDCOM 5.5.1 draft. User statements remain notes unless independently sourced."""
    people = draft.get("people", [])
    lines = [
        "0 HEAD", "1 SOUR Entitlement Navigator Genealogy Interrogator", f"1 DATE {date.today().strftime('%d %b %Y').upper()}",
        "1 GEDC", "2 VERS 5.5.1", "2 FORM LINEAGE-LINKED", "1 CHAR UTF-8",
    ]
    ids = {p["key"]: f"@I{i+1}@" for i, p in enumerate(people)}
    parent_pairs: dict[str, dict[str, str]] = {}
    for rel in draft.get("relationships", []):
        parent_pairs.setdefault(rel["child"], {})[rel["role"]] = rel["parent"]
    fam_index = 1
    fam_for_child: dict[str, str] = {}
    for child, pair in parent_pairs.items():
        fam_for_child[child] = f"@F{fam_index}@"
        fam_index += 1
    for p in people:
        lines += [f"0 {ids[p['key']]} INDI", f"1 NAME {p.get('name','Unknown')}" ]
        if p.get("name_variants"):
            vals = p["name_variants"] if isinstance(p["name_variants"], list) else [p["name_variants"]]
            for v in vals: lines.append(f"1 _AKA {v}")
        if p.get("birth_date") or p.get("birth_place"):
            lines.append("1 BIRT")
            if p.get("birth_date"): lines.append(f"2 DATE {_gedcom_date(p['birth_date'])}")
            if p.get("birth_place"): lines.append(f"2 PLAC {p['birth_place']}")
        if p.get("death_date") or p.get("death_place"):
            lines.append("1 DEAT")
            if p.get("death_date"): lines.append(f"2 DATE {_gedcom_date(p['death_date'])}")
            if p.get("death_place"): lines.append(f"2 PLAC {p['death_place']}")
        if p.get("tribal_or_native_clue"):
            lines.append(f"1 NOTE USER-REPORTED CLUE: {p['tribal_or_native_clue']}")
        if p.get("evidence"):
            lines.append(f"1 NOTE USER-REPORTED SOURCE: {p['evidence']}")
        if p["key"] in fam_for_child:
            lines.append(f"1 FAMC {fam_for_child[p['key']]}")
    for child, pair in parent_pairs.items():
        fid = fam_for_child[child]
        lines.append(f"0 {fid} FAM")
        if pair.get("father") in ids: lines.append(f"1 HUSB {ids[pair['father']]}")
        if pair.get("mother") in ids: lines.append(f"1 WIFE {ids[pair['mother']]}")
        lines.append(f"1 CHIL {ids[child]}")
    lines.append("0 TRLR")
    return "
".join(lines) + "
"

from __future__ import annotations

import hashlib
import re
from collections import deque
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any


REF_RE = re.compile(r"@[^@]+@")
TOP_RE = re.compile(r"^0\s+(@[^@]+@)\s+(\w+)\s*$")
KEYWORDS = {
    "dawes": re.compile(r"\bdawes\b", re.I),
    "allotment": re.compile(r"\ballot(?:ment|ted)?\b", re.I),
    "final_roll": re.compile(r"\bfinal\s+roll\b", re.I),
    "enrollment_roll": re.compile(r"\benroll(?:ment|ed)?\s+(?:record|roll)\b", re.I),
    "trust_land": re.compile(r"\btrust\s+land\b", re.I),
    "restricted_land": re.compile(r"\brestricted\s+land\b", re.I),
    "native_american": re.compile(r"\bnative\s+american\b", re.I),
    "cherokee_nation": re.compile(r"\bcherokee\s+nation\b", re.I),
    "indian_territory": re.compile(r"\bindian\s+territory\b", re.I),
    "probate": re.compile(r"\bprobate\b", re.I),
    "iim": re.compile(r"\bindividual\s+indian\s+money\b|\bIIM\b", re.I),
}


@dataclass
class GedcomRecord:
    record_id: str
    record_type: str
    lines: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    @property
    def refs(self) -> set[str]:
        found: set[str] = set()
        for line in self.lines:
            found.update(REF_RE.findall(line))
        found.discard(self.record_id)
        return found


@dataclass
class Person:
    person_id: str
    name: str = ""
    sex: str = ""
    famc: list[str] = field(default_factory=list)
    fams: list[str] = field(default_factory=list)
    birth_date: str = ""
    birth_place: str = ""
    death_date: str = ""
    death_place: str = ""


@dataclass
class Family:
    family_id: str
    husband: str | None = None
    wife: str | None = None
    children: list[str] = field(default_factory=list)


@dataclass
class GenealogyImport:
    sha256: str
    bytes_count: int
    people_count: int
    family_count: int
    source_count: int
    object_count: int
    focus_person_id: str | None
    focus_resolution: str
    direct_ancestor_count: int
    direct_ancestor_ids: list[str]
    clues: list[dict[str, Any]]
    research_flags: dict[str, bool]

    def to_dict(self, include_private_ids: bool = False) -> dict[str, Any]:
        d = asdict(self)
        if not include_private_ids:
            d.pop("focus_person_id", None)
            d.pop("direct_ancestor_ids", None)
            for clue in d["clues"]:
                clue.pop("record_id", None)
                clue.pop("person_id", None)
                clue.pop("name", None)
        return d


class GedcomGraph:
    def __init__(self, text: str):
        self.text = text
        self.records = self._parse_records(text)
        self.people = self._parse_people()
        self.families = self._parse_families()

    @staticmethod
    def _parse_records(text: str) -> dict[str, GedcomRecord]:
        records: dict[str, GedcomRecord] = {}
        current: GedcomRecord | None = None
        for raw in text.splitlines():
            m = TOP_RE.match(raw.strip())
            if m:
                current = GedcomRecord(m.group(1), m.group(2), [raw])
                records[current.record_id] = current
            elif current is not None:
                current.lines.append(raw)
        return records

    def _parse_people(self) -> dict[str, Person]:
        people: dict[str, Person] = {}
        for rid, rec in self.records.items():
            if rec.record_type != "INDI":
                continue
            p = Person(rid)
            event: str | None = None
            for line in rec.lines[1:]:
                stripped = line.strip()
                parts = stripped.split(" ", 2)
                if len(parts) < 2:
                    continue
                level, tag = parts[0], parts[1]
                value = parts[2] if len(parts) > 2 else ""
                if level == "1":
                    event = tag if tag in {"BIRT", "DEAT"} else None
                    if tag == "NAME": p.name = value.replace("/", "").strip()
                    elif tag == "SEX": p.sex = value
                    elif tag == "FAMC": p.famc.append(value)
                    elif tag == "FAMS": p.fams.append(value)
                elif level == "2" and event:
                    if event == "BIRT" and tag == "DATE": p.birth_date = value
                    elif event == "BIRT" and tag == "PLAC": p.birth_place = value
                    elif event == "DEAT" and tag == "DATE": p.death_date = value
                    elif event == "DEAT" and tag == "PLAC": p.death_place = value
            people[rid] = p
        return people

    def _parse_families(self) -> dict[str, Family]:
        fams: dict[str, Family] = {}
        for rid, rec in self.records.items():
            if rec.record_type != "FAM":
                continue
            f = Family(rid)
            for line in rec.lines[1:]:
                parts = line.strip().split(" ", 2)
                if len(parts) < 3 or parts[0] != "1":
                    continue
                if parts[1] == "HUSB": f.husband = parts[2]
                elif parts[1] == "WIFE": f.wife = parts[2]
                elif parts[1] == "CHIL": f.children.append(parts[2])
            fams[rid] = f
        return fams

    def resolve_focus(self, focus_query: str | None = None) -> tuple[str | None, str]:
        if focus_query:
            needle = focus_query.lower().strip()
            matches = [pid for pid, p in self.people.items() if needle in p.name.lower()]
            if len(matches) == 1:
                return matches[0], "explicit_name_unique_match"
            if len(matches) > 1:
                return None, "explicit_name_ambiguous"
            if focus_query in self.people:
                return focus_query, "explicit_id"
            return None, "explicit_focus_not_found"
        # Ancestry exports commonly place the tree person first, but this is only an assumption.
        first = next(iter(self.people), None)
        return first, "assumed_first_individual"

    def direct_ancestors(self, focus_id: str, max_generations: int = 20) -> dict[str, int]:
        generations: dict[str, int] = {}
        q: deque[tuple[str, int]] = deque([(focus_id, 0)])
        seen = {focus_id}
        while q:
            pid, gen = q.popleft()
            if gen >= max_generations:
                continue
            person = self.people.get(pid)
            if not person:
                continue
            for fam_id in person.famc:
                fam = self.families.get(fam_id)
                if not fam:
                    continue
                for parent in (fam.husband, fam.wife):
                    if parent and parent not in seen:
                        seen.add(parent)
                        generations[parent] = gen + 1
                        q.append((parent, gen + 1))
        return generations

    def related_text(self, record_id: str, depth: int = 1) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        q = deque([(record_id, 0)])
        seen: set[str] = set()
        while q:
            rid, d = q.popleft()
            if rid in seen or rid not in self.records:
                continue
            seen.add(rid)
            rec = self.records[rid]
            out.append((rid, rec.text))
            if d < depth:
                for ref in rec.refs:
                    if ref in self.records:
                        q.append((ref, d + 1))
        return out

    def scan_direct_clues(self, focus_id: str) -> list[dict[str, Any]]:
        gens = self.direct_ancestors(focus_id)
        clues: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for pid, generation in gens.items():
            person = self.people.get(pid)
            for rid, text in self.related_text(pid, depth=1):
                for key, rx in KEYWORDS.items():
                    for m in rx.finditer(text):
                        signature = (pid, rid, key)
                        if signature in seen:
                            continue
                        seen.add(signature)
                        start = max(0, m.start() - 90)
                        end = min(len(text), m.end() + 120)
                        excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
                        clues.append({
                            "clue_type": key,
                            "person_id": pid,
                            "name": person.name if person else "",
                            "generation": generation,
                            "record_id": rid,
                            "excerpt": excerpt,
                            "evidence_state": "USER_FILE_CLUE",
                            "entitlement_effect": "NONE_UNTIL_CORROBORATED",
                        })
        return clues


def import_gedcom_bytes(data: bytes, focus_query: str | None = None) -> tuple[GenealogyImport, GedcomGraph]:
    text = data.decode("utf-8-sig", errors="replace")
    graph = GedcomGraph(text)
    focus_id, resolution = graph.resolve_focus(focus_query)
    ancestors = graph.direct_ancestors(focus_id) if focus_id else {}
    clues = graph.scan_direct_clues(focus_id) if focus_id else []
    flags = {k: any(c["clue_type"] == k for c in clues) for k in KEYWORDS}
    result = GenealogyImport(
        sha256=hashlib.sha256(data).hexdigest(),
        bytes_count=len(data),
        people_count=len(graph.people),
        family_count=len(graph.families),
        source_count=sum(1 for r in graph.records.values() if r.record_type == "SOUR"),
        object_count=sum(1 for r in graph.records.values() if r.record_type == "OBJE"),
        focus_person_id=focus_id,
        focus_resolution=resolution,
        direct_ancestor_count=len(ancestors),
        direct_ancestor_ids=list(ancestors),
        clues=clues,
        research_flags=flags,
    )
    return result, graph


def import_gedcom_file(path: str | Path, focus_query: str | None = None) -> tuple[GenealogyImport, GedcomGraph]:
    return import_gedcom_bytes(Path(path).read_bytes(), focus_query)


def profile_patch_from_genealogy(result: GenealogyImport) -> dict[str, Any]:
    # Derived clues route research but never assert authoritative Dawes/title facts.
    relevant = any(result.research_flags.get(k) for k in ("native_american", "cherokee_nation", "indian_territory", "dawes", "allotment", "trust_land", "probate", "iim"))
    return {
        "has_genealogy_data": True,
        "genealogy_direct_ancestor_count": result.direct_ancestor_count,
        "genealogy_research_relevant": relevant,
        "ancestral_native_clue": bool(result.research_flags.get("native_american") or result.research_flags.get("cherokee_nation") or result.research_flags.get("indian_territory")),
        "genealogy_dawes_clue": bool(result.research_flags.get("dawes") or result.research_flags.get("final_roll")),
        "genealogy_allotment_clue": bool(result.research_flags.get("allotment")),
    }

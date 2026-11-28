#!/usr/bin/env python3
"""Offline checker for kg/humanaios_kg_v0_2_proposal.json (Z1 proposal, authority_effect NONE).

Reads local files and local git only. No network. Does not edit the proposal.

What it separates, per recorded edge:
  source_existence     does the cited record exist where we can look?
  intended_dependency  does the record STATE a dependency, or only name/co-locate?
  approval_evidence    is there a ratification field, who wrote it, is it authenticated?
  observed_outcome     is the target an observed consequence, or only a registered one?

Out-of-scope repositories are reported UNVERIFIABLE_OUT_OF_SCOPE. They are not counted as pass.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "kg" / "humanaios_kg_v0_2_proposal.json"
V01 = ROOT / "kg" / "humanaios_kg_v0_1.json"
LOCAL_REPO = "humanaios-ui/operations"
RELATIONS = {"depends_on", "supported_by", "approved_by", "resulted_in"}
LINK_STATES = {"recorded", "candidate"}
TARGET_PREFIXES = ("registry:", "evidence:", "decision:", "outcome:")
HEX = re.compile(r"^[0-9a-f]{7,40}$")

# Z1 judgments on the semantic dimensions, keyed by edge id. Everything not listed takes the relation default.
# Each value: (verdict, reason). These are reads of commit subjects / registry text, not independent evidence.
DEPENDENCY_JUDGMENT = {
    17: ("STATED_IN_RECORD", "IC-031 Fix field writes the fix as SESSION_RITUALS v6.4 B.0 and B.6"),
    18: ("RATIONALE_ONLY", "IC-031 says F-45 gives the rationale for a protocol-level fix; that is not a runtime dependency"),
    19: ("STATED_IN_RECORD", "IC-030 Fix field: REGISTERED.md fetch is required for registry-touching sessions"),
    20: ("NOT_REPRODUCED", "cited ref IC-031 does not contain the count; this audit's naive parse gives 95 of 153 blocks with a non-null zone2_ratification, not 64 of 139"),
    21: ("NAME_OR_PATH_ONLY", "commit subject names a Z2 review of PR #465; the code does not import or require the gate"),
    22: ("UNVERIFIABLE_OUT_OF_SCOPE", "commit is in a repository outside this session's scope"),
    23: ("UNVERIFIABLE_OUT_OF_SCOPE", "commit is in a repository outside this session's scope"),
    24: ("NAME_OR_PATH_ONLY", "commit subject says registry tests; the diff does not mention REGISTERED.md"),
    25: ("NAME_OR_PATH_ONLY", "evidence_classes.json sits in the ACAT-R comparison directory; no record states the dependency"),
    26: ("STATED_IN_RECORD", "IC-046 title says it extends the IC-044 submission-purity class"),
}
APPROVAL_JUDGMENT = {
    68: ("REGISTRY_FIELD_AGENT_RECORDED", "IC-031 zone2_ratification 'Night - 2026-05-19'; field written by the filing session, no signed hash tied to it"),
    69: ("COMMIT_AGENT_TRANSCRIBED", "ruling file says 'Recorded by: Claude (Z1), as transcription of Z2's decision'; hash is a plain label, not a signature"),
    70: ("COMMIT_AGENT_TRANSCRIBED", "commit author is Claude; the registry itself says the ratification text was unwitnessed until Z2 confirmed in conversation"),
    71: ("REGISTRY_FIELD_AGENT_RECORDED", "IC-058 field names 'Carly (operator)', not 'Night'; no signed hash tied to it"),
    72: ("REGISTRY_FIELD_AGENT_RECORDED", "F-50 field approves the finding, not the registry file; no signed hash tied to it"),
}
OUTCOME_JUDGMENT = {
    76: ("DOCUMENTED_FIX", "IC-031 Fix field describes the protocol change; whether it worked is H-RCO-01, which has no result"),
    77: ("HYPOTHESIS_NOT_OUTCOME", "H-RCO-01 status is CANDIDATE; a registered hypothesis is a plan to measure, not a result"),
    78: ("FINDING_ABOUT_SOURCE", "F-62 is a measured census of the queue; it is a finding about the gate, not a consequence the gate caused"),
    79: ("REGISTERED_CORRECTION", "the misfile correction is in the REGISTERED.md preamble (about line 40), not in the IC-030 entry cited"),
    80: ("FINDING_ABOUT_SOURCE", "IC-065 is a gap found in PR #465 using the comparison engine"),
    81: ("FINDING_ABOUT_SOURCE", "IC-058 is a corpus gap found in the outcome-symmetry work"),
    82: ("FINDING_ABOUT_SOURCE", "IC-044 is a constraint-collapse recurrence found in submission-purity work"),
    83: ("FINDING_ABOUT_SOURCE", "F-56 is a defect found in the scorer"),
    84: ("FINDING_ABOUT_SOURCE", "IC-056 is a reliability gap found in self-report handling"),
    85: ("REGISTERED_CORRECTION", "GRAPH_CONVERGENCE.md is a PROPOSED comparison with total weight 0.0"),
}


# ----------------------------------------------------------------------------- loading
def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def parse_registry(text):
    """id -> {status, zone2_ratification}. Reads each front-matter block that has an id field."""
    out = {}
    for m in re.finditer(r'^\s*id:\s*"?([A-Z][A-Za-z0-9-]+)"?\s*$(.*?)^---', text, re.M | re.S):
        body = m.group(2)
        st = re.search(r"^\s*status:\s*(\S+)", body, re.M)
        z2 = re.search(r'^\s*zone2_ratification:\s*(.+)$', body, re.M)
        z2v = z2.group(1).strip() if z2 else None
        if z2v in ("null", "~", '""', "None"):
            z2v = None
        elif z2v:
            z2v = z2v.strip('"')
        out.setdefault(m.group(1), {"status": st.group(1).strip('"') if st else None, "zone2_ratification": z2v})
    # heading-only entries (no structured front matter) still exist; they carry no status and no ratification field
    for m in re.finditer(r"^#{2,4} ([A-Z][A-Za-z0-9-]*-[A-Za-z0-9-]+)\b", text, re.M):
        out.setdefault(m.group(1), {"status": None, "zone2_ratification": None})
    return out


def git_resolves(ref, root=ROOT):
    p = subprocess.run(["git", "-C", str(root), "cat-file", "-t", ref], capture_output=True, text=True)
    return p.returncode == 0 and p.stdout.strip() == "commit"


class Context:
    def __init__(self, registry, git_ok, file_ok, node_ids):
        self.registry = registry
        self.git_ok = git_ok
        self.file_ok = file_ok
        self.node_ids = node_ids

    @classmethod
    def from_repo(cls, proposal):
        reg = parse_registry((ROOT / "REGISTERED.md").read_text(encoding="utf-8"))
        v01 = {n["id"] for n in load_json(V01)["nodes"]}
        new = {n["id"] for n in proposal.get("new_nodes", [])}
        return cls(reg, git_resolves, lambda p: (ROOT / p).exists(), v01 | new)


# ----------------------------------------------------------------------------- helpers
def target_kind(target):
    return target.split(":", 1)[0] if ":" in target else "node"


def registry_id(edge):
    t = edge["target"]
    if t.startswith(("registry:", "decision:", "outcome:")):
        rid = t.split(":", 1)[1]
        return rid if re.match(r"^[A-Z]", rid) and "-" in rid else None
    return None


def is_hypothesis(rid):
    return bool(rid) and (rid.startswith("H-") or rid.startswith("H_"))


def edge_local(edge):
    b = edge.get("basis", {})
    return b.get("repo") in (None, LOCAL_REPO)


def supporting_edges(proposal):
    """Only recorded edges count as support. Candidates do not. Nothing here is ratified."""
    return [e for e in proposal["edges"] if e.get("link_state") == "recorded"]


# ----------------------------------------------------------------------------- validation
def validate(proposal, ctx):
    f = []

    def add(eid, code, sev, msg):
        f.append({"edge": eid, "code": code, "severity": sev, "message": msg})

    if proposal.get("authority_effect") != "NONE":
        add(None, "E_SCHEMA", "error", "authority_effect must be NONE")
    seen = set()
    for e in proposal["edges"]:
        eid = e.get("id")
        if eid in seen:
            add(eid, "E_SCHEMA", "error", "duplicate edge id")
        seen.add(eid)
        for k in ("source", "target", "relation", "link_state", "status", "basis"):
            if k not in e:
                add(eid, "E_SCHEMA", "error", "missing field " + k)
        if e.get("relation") not in RELATIONS:
            add(eid, "E_SCHEMA", "error", "relation not in vocabulary")
        if e.get("link_state") not in LINK_STATES:
            add(eid, "E_SCHEMA", "error", "link_state not in vocabulary")
        if e.get("status") != "unratified":
            add(eid, "E_CANDIDATE_PROMOTION", "error", "status must stay unratified; only Z2 ratifies")
        src, tgt = e.get("source", ""), e.get("target", "")
        if src not in ctx.node_ids:
            add(eid, "E_NODE_REF", "error", "source node not defined in v0.1 or new_nodes: " + src)
        if ":" not in tgt and tgt not in ctx.node_ids:
            add(eid, "E_NODE_REF", "error", "target node not defined in v0.1 or new_nodes: " + tgt)
        if ":" in tgt and not tgt.startswith(TARGET_PREFIXES):
            add(eid, "E_REF_BROKEN", "error", "unknown target namespace: " + tgt)

        b = e.get("basis", {})
        rec = e.get("link_state") == "recorded"
        # candidate promotion: a recorded edge must point at a dated record, not at an inference
        if rec and (b.get("type") == "inference" or not b.get("ref")):
            add(eid, "E_CANDIDATE_PROMOTION", "error", "recorded edge has inference basis or empty ref")
        if not rec and not b.get("note"):
            add(eid, "E_CANDIDATE_PROMOTION", "error", "candidate edge must say why it is only a candidate")

        # reference resolution
        rid = registry_id(e)
        if rid and rid != "unrecorded" and (tgt.startswith(("registry:", "decision:", "outcome:"))):
            if b.get("type") == "registry" and rid not in ctx.registry and not tgt.startswith("outcome:"):
                add(eid, "E_REF_BROKEN", "error", "registry id not found in REGISTERED.md: " + rid)
        if b.get("type") == "registry" and b.get("ref") and b["ref"] not in ctx.registry:
            add(eid, "E_REF_BROKEN", "error", "basis ref not found in REGISTERED.md: " + b["ref"])
        if b.get("type") == "commit":
            if edge_local(e):
                if not ctx.git_ok(b.get("ref", "")):
                    add(eid, "E_REF_BROKEN", "error", "commit does not resolve in this checkout: " + str(b.get("ref")))
        if b.get("type") == "file" and edge_local(e):
            if not ctx.file_ok(b.get("ref", "")):
                add(eid, "E_REF_BROKEN", "error", "file not found: " + str(b.get("ref")))
        if tgt.startswith("evidence:") and edge_local(e):
            tail = tgt.split(":", 1)[1]
            if HEX.match(tail) and not ctx.git_ok(tail):
                add(eid, "E_REF_BROKEN", "error", "evidence commit does not resolve: " + tail)
        if b.get("type") in ("commit", "file") and not edge_local(e):
            add(eid, "U_OUT_OF_SCOPE", "info", "repository outside session scope: " + str(b.get("repo")))

        # false causal link: a registered hypothesis is not a result
        if e.get("relation") == "resulted_in" and rec:
            if is_hypothesis(rid):
                reg = ctx.registry.get(rid, {})
                if reg.get("status") != "RESOLVED":
                    add(eid, "E_FALSE_CAUSAL", "error",
                        "resulted_in target %s is a hypothesis with status %s, not a recorded result" % (rid, reg.get("status")))
            if b.get("type") == "inference":
                add(eid, "E_FALSE_CAUSAL", "error", "resulted_in recorded on an inference")

        # missing approval
        if e.get("relation") == "approved_by":
            if tgt == "decision:unrecorded":
                if rec:
                    add(eid, "E_MISSING_APPROVAL", "error", "no decision record exists; edge must be candidate")
            elif rec:
                reg = ctx.registry.get(rid or "", {})
                has_field = bool(reg.get("zone2_ratification"))
                has_commit = b.get("type") == "commit"
                if not (has_field or has_commit):
                    add(eid, "E_MISSING_APPROVAL", "error", "approved_by has neither a zone2_ratification field nor a ratification commit")
            if e.get("status") != "unratified":
                add(eid, "E_MISSING_APPROVAL", "error", "approved_by does not make an edge ratified")

    # same registry entry used four ways for one source inflates support
    by = {}
    for e in proposal["edges"]:
        if e.get("link_state") != "recorded":
            continue
        r = e.get("basis", {}).get("ref") if e.get("basis", {}).get("type") == "registry" else None
        if r:
            by.setdefault((e["source"], r), []).append(e)
    for (s, r), es in by.items():
        rel = {x["relation"] for x in es}
        if len(rel) >= 2:
            add(None, "W_SELF_CORROBORATION", "warning",
                "%s cites %s under %d relations (%s); one record, counted as %d" % (s, r, len(rel), ", ".join(sorted(rel)), len(es)))
    return f


def preservation_checks(proposal):
    """Things that must not be invented or filled in."""
    out = []
    nodes = {n["id"]: n for n in proposal["new_nodes"]}
    if nodes.get("C19", {}).get("first_dated") != "":
        out.append("C19 first_dated must stay empty (unknown)")
    touched = set()
    for e in proposal["edges"]:
        touched.add(e["source"])
        touched.add(e["target"])
    for n in ("A02", "A06"):
        if n in touched:
            out.append(n + " must stay unlinked: no dated artifact was found")
    return out


# ----------------------------------------------------------------------------- audit
def audit_recorded(proposal, ctx):
    rows = []
    for e in proposal["edges"]:
        if e["link_state"] != "recorded":
            continue
        b = e["basis"]
        rel = e["relation"]
        if b.get("type") in ("commit", "file") and not edge_local(e):
            src = "UNVERIFIABLE_OUT_OF_SCOPE"
        elif b.get("type") == "commit":
            src = "VERIFIED" if ctx.git_ok(b["ref"]) else "BROKEN"
        elif b.get("type") == "file":
            src = "VERIFIED" if ctx.file_ok(b["ref"]) else "BROKEN"
        elif b.get("type") == "registry":
            src = "VERIFIED" if b["ref"] in ctx.registry else "BROKEN"
        else:
            src = "BROKEN"
        row = {"edge": e["id"], "source": e["source"], "relation": rel, "target": e["target"],
               "basis_type": b.get("type"), "basis_ref": b.get("ref"), "basis_repo": b.get("repo"),
               "source_existence": src,
               "intended_dependency": "NOT_APPLICABLE", "approval_evidence": "NOT_APPLICABLE",
               "observed_outcome": "NOT_APPLICABLE", "authenticated": False, "independently_observed": False,
               "reason": ""}
        if rel == "depends_on":
            v, why = DEPENDENCY_JUDGMENT.get(e["id"], ("NOT_JUDGED", "no judgment recorded"))
            row["intended_dependency"], row["reason"] = v, why
        elif rel == "approved_by":
            v, why = APPROVAL_JUDGMENT.get(e["id"], ("NOT_JUDGED", "no judgment recorded"))
            row["approval_evidence"], row["reason"] = v, why
        elif rel == "resulted_in":
            v, why = OUTCOME_JUDGMENT.get(e["id"], ("NOT_JUDGED", "no judgment recorded"))
            row["observed_outcome"], row["reason"] = v, why
        else:
            row["reason"] = "supported_by asserts only that the record exists"
        rows.append(row)
    return rows


def apply_overlay(proposal, overlay):
    """Return a corrected COPY. The proposal file is left as it is."""
    out = json.loads(json.dumps(proposal))
    by = {e["id"]: e for e in out["edges"]}
    for c in overlay["corrections"]:
        e = by[c["edge"]]
        if c["action"] == "downgrade_to_candidate":
            e["link_state"] = "candidate"
            e["basis"] = dict(e["basis"], note=c["new_note"])
        elif c["action"] == "retarget_ref":
            e["basis"] = dict(e["basis"], ref=c["new_ref"], type=c.get("new_type", e["basis"]["type"]))
        elif c["action"] == "note_correction":
            e["basis"] = dict(e["basis"], note=c["new_note"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal", default=str(PROPOSAL))
    ap.add_argument("--overlay", default=None, help="apply a corrections overlay in memory before checking")
    ap.add_argument("--audit-out", default=None)
    a = ap.parse_args(argv)
    prop = load_json(a.proposal)
    if a.overlay:
        prop = apply_overlay(prop, load_json(a.overlay))
    ctx = Context.from_repo(prop)
    findings = validate(prop, ctx)
    pres = preservation_checks(prop)
    rows = audit_recorded(prop, ctx)
    if a.audit_out:
        pathlib.Path(a.audit_out).write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    errs = [x for x in findings if x["severity"] == "error"]
    for x in findings:
        print("%-8s %-22s edge=%s %s" % (x["severity"], x["code"], x["edge"], x["message"]))
    for p in pres:
        print("error    E_PRESERVATION        " + p)
    print("edges=%d recorded=%d candidate=%d errors=%d" % (
        len(prop["edges"]), len(supporting_edges(prop)), len(prop["edges"]) - len(supporting_edges(prop)), len(errs) + len(pres)))
    return 1 if (errs or pres) else 0


if __name__ == "__main__":
    sys.exit(main())

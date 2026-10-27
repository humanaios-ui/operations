#!/usr/bin/env python3
"""Local-only static HTML view of E0. No JavaScript, network, or authority."""
import argparse
from html import escape
import json
from pathlib import Path


def safe(value):
    return escape(str(value), quote=True)


def table(headers, rows, empty="No records"):
    h = "".join("<th>" + safe(x) + "</th>" for x in headers)
    body = "".join(
        "<tr>" + "".join("<td>" + safe(x) + "</td>" for x in row) + "</tr>"
        for row in rows
    )
    if not body:
        body = '<tr><td colspan="' + str(len(headers)) + '">' + safe(empty) + "</td></tr>"
    return "<table><thead><tr>" + h + "</tr></thead><tbody>" + body + "</tbody></table>"


def render(report):
    if report.get("schema") != "humanaios.attractor_observatory.e0":
        raise ValueError("unexpected report schema")
    if report.get("authority_effect") != "NONE" or report.get("execution") != "DISABLED":
        raise ValueError("report contains authority or execution claim")
    inside = report["internal"]
    returns = report["observed_returns"]
    external = report["external_conversion"]
    cycles = inside["strongly_connected_components"]
    component_rows = [
        (", ".join(c["node_ids"]), c["size"], c["reachable_from_start_count"],
         "yes" if c["cyclic"] else "no", "yes" if c["terminal"] else "no")
        for c in cycles
    ]
    return_rows = [
        (x["node_id"], x["extra_visits_in_trails"])
        for x in (returns["repeated_returns"] or [])
    ]
    outcome_rows = [
        (stage, (external["outcomes"] or {}).get(stage, 0),
         (external.get("separately_review_attested_outcomes") or {}).get(stage, 0))
        for stage in ("RESOURCE_ACQUIRED", "OBJECTIVE_COMPLETED", "RECOVERY_BENEFIT_DELIVERED")
    ] if external["state"] != "NOT_MEASURED" else []
    process_rows = [
        (p["process_id"], p["RESOURCE_ACQUIRED"], p["OBJECTIVE_COMPLETED"],
         p["RECOVERY_BENEFIT_DELIVERED"], p["review_attested"])
        for p in (external["by_process"] or [])
    ]
    head = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HumanAIOS · Attractor Observatory E0</title>
<style>
:root{color-scheme:dark;--paper:#e7f1ec;--muted:#9ab4ad;--gold:#d8b96b;--panel:#162b2b;--line:#2a4846}
*{box-sizing:border-box}body{margin:0;background:#0b191b;color:var(--paper);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1180px;margin:0 auto;padding:42px 22px 80px}
h1{font-size:clamp(30px,5vw,52px);letter-spacing:-.05em;margin:0}
h2{font-size:23px;margin:0 0 12px}p{color:var(--muted)}
.eyebrow{color:var(--gold);font-size:12px;text-transform:uppercase;letter-spacing:.18em;font-weight:800}
.lead{font-size:18px;max-width:810px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px;margin:26px 0}
.card,section{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:22px}
.card strong{display:block;font-size:29px;color:#f4dfab;line-height:1.3;overflow-wrap:anywhere}
.card span{font-size:13px;color:var(--muted)}
section{margin:20px 0;overflow:auto}table{width:100%;border-collapse:collapse;text-align:left;font-size:14px}
th{color:var(--gold);font-size:12px;text-transform:uppercase;letter-spacing:.05em}
td,th{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}
td:first-child{overflow-wrap:anywhere;max-width:380px}
.note{padding:14px 18px;border-left:3px solid var(--gold);background:#20342f;border-radius:5px;color:#e4dfc9}
.small{font-size:13px}.status{font-family:ui-monospace,SFMono-Regular,monospace;overflow-wrap:anywhere}
</style></head><body><main>
<div class="eyebrow">HumanAIOS / observability / E0</div>
<h1>Where do the paths lead?</h1>
<p class="lead">Two separate questions. Where can internal paths return?
Where do recorded real-world outcomes appear? A network loop is not a human benefit.</p>
<div class="note">READ ONLY · AUTHORITY NONE · NO LIVE SYSTEM CHECKS ·
Receipts in this observer are not independently authenticated.</div>"""
    cards = [
        ("Graph nodes", inside["node_count"]),
        ("Graph edges", inside["edge_count"]),
        ("Largest cyclic group", inside["largest_cyclic_component_size"]),
        ("First-edge loop starts", inside["first_stored_edge_loop_starts"]),
        ("Observed returns", returns["state"]),
        ("External conversion", external["state"]),
    ]
    bits = [head, '<div class="grid">']
    for label, value in cards:
        bits.append('<div class="card"><span>' + safe(label) + '</span><strong>' + safe(value) + '</strong></div>')
    bits.append("</div>")
    bits.append('<section><div class="eyebrow">01 · Internal / structural</div><h2>Connected cycles and exits</h2>')
    bits.append('<p>Reach = number of starting nodes that can reach the component by some directed path. It is not visit frequency.</p>')
    bits.append(table(["Node IDs", "Size", "Reach", "Cycle", "Terminal"], component_rows))
    bits.append('<p class="small">First-edge policy: ' + safe(inside["first_stored_edge_policy"]) + '</p></section>')
    bits.append('<section><div class="eyebrow">02 · Internal / observed</div><h2>Repeated actual visits</h2>')
    bits.append('<p class="status">' + safe(returns["state"]) + '</p>')
    bits.append(table(["Node", "Extra visits within trail"], return_rows,
                      "No authenticated trails supplied; not measured." if returns["state"] == "NOT_MEASURED" else "No revisits in supplied trail records."))
    bits.append('</section>')
    bits.append('<section><div class="eyebrow">03 · External / conversion</div><h2>Outcome assertions by stage</h2>')
    bits.append('<p class="status">' + safe(external["state"]) + '</p>')
    bits.append(table(["Stage", "Documented claims", "Separate reviewer attested"],
                      outcome_rows, "No outcome records supplied; not measured."))
    bits.append('<h2>Associated processes</h2>')
    bits.append(table(["Process", "Resources", "Objectives", "Recovery benefits", "Review-attested"],
                      process_rows, "No process-linked outcomes in supplied records."))
    bits.append('<p class="small">Unmapped process IDs: ' +
                safe(", ".join(external.get("unmapped_process_ids", [])) or "none reported") + '</p></section>')
    bits.append('<p class="small">Source graph generated at: ' + safe(report.get("graph_generated_at")) +
                ' · Snapshot SHA256: ' + safe((report.get("inputs") or {}).get("graph_sha256", "not supplied")) +
                '</p><p class="note">Not a deployment receipt, eligibility check, grant award, profit record, or beneficiary audit.</p>')
    bits.append("</main></body></html>")
    return "".join(bits)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = json.loads(Path(args.input).read_text(encoding="utf-8"))
    Path(args.output).write_text(render(report), encoding="utf-8")


if __name__ == "__main__":
    main()

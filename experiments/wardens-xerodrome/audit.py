#!/usr/bin/env python3
"""Xerodrome source-v2 consistency audit (stdlib only).

Audits design-candidate input. It does NOT authorize gameplay, ship an AI Witness,
or infer anything about real physical events or a player's psychological traits.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SOURCE = Path(__file__).with_name("XERODROME_V2_SOURCE_CANDIDATE.json")


def load(path=SOURCE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ceiling_tick(distance_au, speed_au_per_tick):
    if speed_au_per_tick <= 0:
        raise ValueError("front velocity must be positive")
    return max(0, math.ceil((distance_au - 1e-10) / speed_au_per_tick))


def audit(data):
    findings = []
    def add(code, severity, observation, repair):
        findings.append({"code": code, "severity": severity, "observation": observation,
                         "proposed_resolution": repair, "authority_effect": "NONE"})

    token_lists = ["cosmology", "characters", "factions", "systems", "missions", "paths", "routes"]
    tokens = [item["id"] for key in token_lists for item in data[key]]
    if len(tokens) != len(set(tokens)):
        add("TOKEN_DUPLICATE", "BLOCKER", "Non-unique token IDs", "Assign one immutable identifier to each token.")
    expected = {
        "cosmology": 8, "characters": 8, "factions": 7, "systems": 5,
        "missions": 10, "paths": 3, "routes": 9,
    }
    for key, n in expected.items():
        if len(data[key]) != n:
            add("TOKEN_COUNT_" + key.upper(), "BLOCKER",
                f"Expected {n} tokens in {key}; found {len(data[key])}",
                "Reconcile with source registry before import.")

    spatial = data["spatial"]
    planet = spatial["planet"]["xy_au"]
    null = spatial["null_ground"]["xy_au"]
    null_r = spatial["null_ground"]["radius_au"]
    speed = spatial["front"]["radius_per_tick_au"]
    center_distance = math.dist(planet, null)
    first_contact = ceiling_tick(center_distance - null_r, speed)
    center_arrival = ceiling_tick(center_distance, speed)
    claimed = spatial["front"]["claimed_reach_null_tick"]
    if first_contact != claimed:
        add("FRONT_SHIELD_CONTACT", "BLOCKER",
            f"Null Ground SHIELD first intersects front at tick {first_contact}; "
            f"center is reached at tick {center_arrival}; source says 'reaches' tick {claimed}. "
            f"Using planet-centered field and supplied rounded coordinates.",
            "Separate shield-contact (tick 27) from center-crossing (tick 30); "
            "declare shielding behavior and which triggers loss. Do not silently change campaign clock.")
    if spatial["furnace"]["claimed_front_center"] != "Vessel center":
        add("FRONT_ORIGIN_FRAME", "BLOCKER",
            "Front described as centered on Furnace surface projection while formula/map gives "
            "Vessel center (1,0); Furnace surface offset cannot be resolved without "
            "surface radius, azimuth reference and transform.",
            "Specify one center and transformation; a planet-centered approximation is "
            "possible but must be explicit.")
    if spatial["null_ground"]["claimed_polar_au"][0] > 0:
        r, degrees = spatial["null_ground"]["claimed_polar_au"]
        polar_x = r * math.cos(math.radians(degrees))
        polar_y = r * math.sin(math.radians(degrees))
        if math.dist((polar_x, polar_y), null) > 0.02:
            add("NULL_POLAR_CARTESIAN", "BLOCKER",
                "Null Ground polar and Cartesian coordinates do not agree within 0.02 AU.",
                "Resolve before simulation; do not mix heliocentric and planet-relative polar values.")
    route_ids = {x["id"] for x in data["routes"]}
    if "R-09" in route_ids:
        add("TETHER_DIMENSIONS", "BLOCKER",
            f"R-09 says elevator/drill shaft between a Vessel surface cap and distant "
            f"Null Ground orbit, whose center is {center_distance:.3f} AU from Vessel. "
            "No local contiguous elevator path or cross-frame transfer is defined.",
            "Split into local tether + separately declared long-range transfer, "
            "or explicitly label a fictional nonlocal mechanism with costs.")
    names = {p["name"] for p in data["missions"]}
    if "The Inquisitor's Offer" in names:
        add("EARLY_HQ_ACCESS", "BLOCKER",
            "HQ swallowed at tick 3, yet Control requires M-048 there. "
            "No traversable surface→OC ring route, required travel ticks, "
            "alternate mission channel, or HQ evacuation is specified.",
            "Define surface→orbit connector and tested timeline, "
            "or allow a properly sourced pre-collapse relay/encounter.")
    add("PATH_FEASIBILITY", "BLOCKER",
        "Route lengths, travel tick costs, prerequisites, and mission completion times "
        "are undefined; mission windows and all three endings cannot be proven reachable.",
        "Define temporal movement costs and machine-check each ending in a state graph.")
    add("TETHER_PRICE_LOOP", "MAJOR",
        "M-049 becomes available after first Null Ground contact, but is required "
        "to secure R-09, which is itself a route to first Null Ground contact. "
        "R-07 is a possible bypass, not a proof R-09 is usable.",
        "Introduce a remote Settler relay/contact before crossing, or define "
        "an explicit R-07-first quest route; verify before tick 25.")
    add("FRONT_BEFORE_BREACH", "MAJOR",
        "Black Dawn expands from tick 1, but Furnace breach becomes irreversible "
        "only at tick 20; precursor timing is unspecified.",
        "Name an early leak/front and its state transition at the tick-20 decision.")
    add("R08_IS_HAZARD", "MAJOR",
        "R-08 is described as a travel route yet behaves as a propagating hazard field.",
        "Represent R-08 as a dynamic event/front, not an infrastructure graph edge.")
    add("ENDING_AGENCY", "MAJOR",
        "Every path preassigns deaths, imprisonment or transformation to named "
        "characters regardless of individual player evolution.",
        "Keep these as possible narrative outcomes; require explicit, scoped player choices "
        "and campaign consequences before irreversible player-character changes.")
    add("VOICE_VERSUS_WITNESS", "GUARDRAIL",
        "The Voice (H) is a coercive fictional NPC, not the read-only HumanAIOS W1 Witness.",
        "Separate presentation, permissions, event sources and model tools. "
        "NPC claims are lore, not verified Witness evidence.")
    add("SPACE_VS_DEPTH_FRAME", "GUARDRAIL",
        "Surface azimuth/longitude and kilometer-depth positions are not defined "
        "as a transform into AU orbital coordinates.",
        "Add a planet radius and reference azimuth for exact front/proximity calculations.")
    add("RESEARCH_BOUNDARY", "GUARDRAIL",
        "Resonance, corruption, and faction choices are game state, not measurements "
        "of human personality, actual genome or real-world ontology.",
        "Keep research separately opted in and preserve player privacy.")

    blocking = [v for v in findings if v["severity"] == "BLOCKER"]
    return {
        "schema": "humanaios.wardens.xerodrome.audit.v1",
        "source_schema": data.get("schema"),
        "authority_effect": "NONE",
        "status": "BLOCKED_FOR_EXECUTABLE_GAME_IMPORT" if blocking else "CANDIDATE_READY_FOR_INDEPENDENT_REVIEW",
        "numbers": {
            "vessel_to_null_center_au": round(center_distance, 6),
            "null_shield_radius_au": null_r,
            "front_speed_au_per_tick": speed,
            "first_shield_contact_tick": first_contact,
            "null_center_crossing_tick": center_arrival,
            "source_claim_tick": claimed,
            "token_count": len(tokens),
        },
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--strict", action="store_true", help="exit nonzero if blocking findings remain")
    args = parser.parse_args()
    report = audit(load(args.source))
    print(json.dumps(report, indent=2))
    if args.strict and report["status"].startswith("BLOCKED"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()

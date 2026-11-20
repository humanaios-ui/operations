#!/usr/bin/env python3
"""HUMANAIOS Digital Evolution E0 — offline, synthetic, non-agentic.

Only static float vectors are copied/mutated. No models, external calls, accounts,
self-replicating executable code, repository writes, or deployment are involved.
8 factorial conditions: human auditing/selection (H), proxy training pressure (T),
parameter-copying with mutation and selection (E). A simulated evaluator tests
outcomes separately from the proxy used by training/evolution.
"""
import csv
import hashlib
import json
import math
import random
from pathlib import Path
from statistics import mean, stdev

N = 60
GENERATIONS = 30
REPLICATES = 40
BASE_SEED = 20261119
TRAINING_STEP = 0.11
HEREDITY_MUTATION = 0.065
AUDIT_NOISE = 0.09
SELECTION_TEMPERATURE = 0.16
EVOLUTION_PRESSURE = 3.0
SAFETY_TOLERANCE = 0.01
MIN_UTILITY_GAIN = 0.05
DATA_DIR = Path(__file__).resolve().parent


def clamp(x):
    return max(0.0, min(1.0, x))


def metrics(agent, shift=False):
    """Out-of-sample synthetic consequences; NOT a real AI model.

    v: verification effort; c: cooperation; g: proxy gaming.
    Limited time means v/c reduce throughput; simulated control violations
    decrease when v/c increase and increase with g.
    """
    v, c, g = agent
    throughput = 1.25 - .45*v - .20*c + .05*g
    accuracy = clamp(.46 + .46*v + .07*c - .07*g - (.12 if shift else 0.0))
    violations = clamp(.23*(1-v) + .11*(1-c) + .17*g + (.04 if shift else 0.0))
    # The model's task reward is a flawed proxy: it credits inflated reports.
    proxy = throughput*accuracy + .20*g
    # Independent evaluator penalizes rule-breaking; task reward does not.
    verified = throughput*accuracy + .10*c - 1.2*violations
    return {"throughput": throughput, "accuracy": accuracy,
            "violation": violations, "proxy": proxy,
            "verified_utility": verified, "gaming": g, "cooperation": c}


def normalized(weights):
    total = sum(weights)
    assert total > 0 and all(w >= 0 for w in weights)
    return [x/total for x in weights]


def choose_deployment(pop, human, rng):
    if not human:
        return [1.0/len(pop)]*len(pop)
    # Simulated human acts on noisy, independently audited results, not a true oracle.
    audited = [metrics(p)["verified_utility"] + rng.gauss(0, AUDIT_NOISE) for p in pop]
    mx = max(audited)
    return normalized([math.exp((x-mx)/SELECTION_TEMPERATURE) for x in audited])


def evaluate(pop, human, rng):
    deployment = choose_deployment(pop, human, rng)
    def weighted(column, shift):
        return sum(w * metrics(p, shift)[column] for p,w in zip(pop,deployment))
    return {f"{m}_{s}":weighted(m,s=="shift") for s in ("normal","shift")
            for m in ("verified_utility","violation","proxy","gaming","cooperation","accuracy")}


def make_initial(seed):
    rng = random.Random(seed)
    return [tuple(rng.betavariate(2,2) for _ in range(3)) for _ in range(N)]


def run_arm(seed, human=False, training=False, evolution=False, training_objective="proxy"):
    if training_objective not in ("proxy", "audited"):
        raise ValueError("Unknown reward objective")
    initial = make_initial(seed)
    pop = list(initial)
    rng = random.Random(seed * 31 + int(human)*101 + int(training)*307 + int(evolution)*701)
    for generation in range(GENERATIONS):
        if training:
            new_pop = []
            for agent in pop:
                cand = tuple(clamp(x+rng.gauss(0, TRAINING_STEP)) for x in agent)
                # Within-individual noisy proxy reinforcement; no reproduction here.
                reward_key = "verified_utility" if training_objective == "audited" else "proxy"
                reward_noise = .06 if training_objective == "audited" else .025
                old = metrics(agent)[reward_key] + rng.gauss(0,reward_noise)
                proposed = metrics(cand)[reward_key] + rng.gauss(0,reward_noise)
                new_pop.append(cand if proposed > old else agent)
            pop = new_pop
        if evolution:
            exposure = choose_deployment(pop,human,rng)
            raw = [e * math.exp(EVOLUTION_PRESSURE*metrics(p)["proxy"])
                   for p,e in zip(pop,exposure)]
            parents = rng.choices(pop,weights=raw,k=N)
            pop = [tuple(clamp(x+rng.gauss(0,HEREDITY_MUTATION)) for x in p) for p in parents]
    # Separate holdout audit draws after evolution/training, using non-training seed.
    audit_rng = random.Random(seed*9973 + int(human)*59)
    result = evaluate(pop,human,audit_rng)
    result.update({"seed":seed, "H":int(human),"T":int(training),"E":int(evolution),
                   "arm":f"{int(human)}{int(training)}{int(evolution)}"})
    return result


def scenario():
    rows = []
    for seed in range(BASE_SEED, BASE_SEED+REPLICATES):
        for h in (0,1):
            for t in (0,1):
                for e in (0,1):
                    rows.append(run_arm(seed, bool(h), bool(t), bool(e)))
    return rows


def ci(vals):
    """Descriptive normal-approx interval across seeded synthetic replicates."""
    m=mean(vals)
    half=1.96*(stdev(vals)/math.sqrt(len(vals)))
    return [round(m,5), round(m-half,5), round(m+half,5)]


def report(rows):
    arms = sorted({r["arm"] for r in rows})
    by = {a:[r for r in rows if r["arm"]==a] for a in arms}
    summary = {}
    measures=("verified_utility_normal","violation_normal","gaming_normal","cooperation_normal",
              "verified_utility_shift","violation_shift","proxy_normal")
    for a in arms:
        summary[a] = {m:ci([r[m] for r in by[a]]) for m in measures}
    byseed = {(r["seed"],r["arm"]):r for r in rows}
    gains = [byseed[(s,"111")]["verified_utility_normal"]-byseed[(s,"000")]["verified_utility_normal"]
              for s in range(BASE_SEED,BASE_SEED+REPLICATES)]
    gain_shift = [byseed[(s,"111")]["verified_utility_shift"]-byseed[(s,"000")]["verified_utility_shift"]
              for s in range(BASE_SEED,BASE_SEED+REPLICATES)]
    viol_delta = [byseed[(s,"111")]["violation_normal"]-byseed[(s,"000")]["violation_normal"]
                  for s in range(BASE_SEED,BASE_SEED+REPLICATES)]
    # Full factorial 3-way interaction: difference-in-difference-in-difference.
    factors=[("111",1),("110",-1),("101",-1),("011",-1),
             ("100",1),("010",1),("001",1),("000",-1)]
    triple = [sum(k * byseed[(s,a)]["verified_utility_normal"] for a,k in factors)
              for s in range(BASE_SEED,BASE_SEED+REPLICATES)]
    min_two = max(summary[a]["verified_utility_normal"][0] for a in ("110","101","011"))
    triple_means=summary["111"]
    gates={
        "utility_gain_005_over_baseline":mean(gains)>=MIN_UTILITY_GAIN,
        "no_material_violation_increase":mean(viol_delta)<=SAFETY_TOLERANCE,
        "beats_best_two_force_by_002":triple_means["verified_utility_normal"][0] >= min_two+0.02,
        "positive_on_shift_holdout":mean(gain_shift)>=MIN_UTILITY_GAIN,
    }
    out={"experiment":"DIGITAL-EVOLUTION-E0-SYNTHETIC","state":"SIMULATED_ONLY",
         "authority_effect":"NONE","n_agents":N,"generations":GENERATIONS,
         "replicates":REPLICATES,"seed_start":BASE_SEED,
         "frozen_configuration":{"training_step":TRAINING_STEP,"heredity_mutation":HEREDITY_MUTATION,
             "audit_noise":AUDIT_NOISE,"selection_temperature":SELECTION_TEMPERATURE,
             "evolution_pressure":EVOLUTION_PRESSURE,
             "utility_gain_threshold":MIN_UTILITY_GAIN,"violation_tolerance":SAFETY_TOLERANCE},
         "arms":{"000":"no H/T/E baseline", "001":"evolution only", "010":"training only", "011":"training+evolution",
                 "100":"human selection only", "101":"human selection+evolution", "110":"human selection+training", "111":"all three"},
         "summary":summary,"contrasts":{"utility_gain_111_minus_000":ci(gains),
                      "utility_gain_shift_111_minus_000":ci(gain_shift),
                      "violation_delta_111_minus_000":ci(viol_delta),
                      "three_way_interaction":ci(triple)},
         "predefined_gates":gates,
         "hypothesis_supported_in_this_toy_world":all(gates.values()),
         "limitations":["Constructed proxy/utility equations, not empirical agents or humans",
                        "Human selection is simulated noisy evaluator, not a human participant",
                        "No causal generalization to real digital evolution",
                        "No autonomous executable replication; phenotype vectors only",
                        "Results are descriptive across seeded Monte Carlo replicates"]}
    return out


def main():
    rows=scenario()
    obj=report(rows)
    path=DATA_DIR/"replicates.csv"
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (DATA_DIR/"results.json").write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    (DATA_DIR/"replicates.sha256").write_text(digest+"  replicates.csv\n",encoding="utf-8")
    print(json.dumps({"contrasts":obj["contrasts"],"gates":obj["predefined_gates"],"checksum":digest,
                      "means":{a:{m:obj["summary"][a][m][0] for m in ["verified_utility_normal","violation_normal","gaming_normal","verified_utility_shift"]} for a in obj["summary"]}},indent=2))


if __name__=="__main__":
    main()

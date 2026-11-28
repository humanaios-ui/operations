#!/usr/bin/env python3
"""Post-hoc sensitivity analyses, kept separate from original preregistered contrasts."""
import json
from statistics import mean
from pathlib import Path
import digital_evolution_e0 as d

def run():
    seeds = range(20270001,20270041)
    conditions = {
      "new_seeds_standard_audit": (.09,"proxy"),
      "noisier_human_audit": (.22,"proxy"),
      "noisy_independent_outcome_training": (.09,"audited")
    }
    orig=d.AUDIT_NOISE
    out={}
    for label,(audit_noise,reward) in conditions.items():
        d.AUDIT_NOISE=audit_noise
        data=[]
        for seed in seeds:
            a={n:d.run_arm(seed,bool(int(n[0])),bool(int(n[1])),bool(int(n[2])),training_objective=reward)
                for n in ('000','101','111')}
            data.append({k:a[k]['verified_utility_normal'] for k in a})
            data[-1].update({k+"_violation":a[k]['violation_normal'] for k in a})
            data[-1].update({k+"_gaming":a[k]['gaming_normal'] for k in a})
        out[label] = {
            "replicates":len(data),"human_audit_noise":audit_noise,"training_objective":reward,
            "means":{arm:round(mean(r[arm] for r in data),5) for arm in ('000','101','111')},
            "mean_111_minus_101":round(mean(r['111']-r['101'] for r in data),5),
            "mean_111_minus_000":round(mean(r['111']-r['000'] for r in data),5),
            "mean_111_violations":round(mean(r['111_violation'] for r in data),5),
            "mean_111_gaming":round(mean(r['111_gaming'] for r in data),5),
        }
    d.AUDIT_NOISE=orig
    (Path(__file__).parent/'robustness_results.json').write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    run()

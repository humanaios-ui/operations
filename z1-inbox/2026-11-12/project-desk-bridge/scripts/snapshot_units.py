#!/usr/bin/env python3
"""Read-only extract of the ratified RESOURCE_UNITS.yaml into vendor/resource-units.snapshot.json.
Usage: snapshot_units.py <path-to-RESOURCE_UNITS.yaml> <source-commit> > vendor/resource-units.snapshot.json
Never writes to the operations repo. The snapshot pins the source sha256 so drift is detectable."""
import hashlib, json, sys
import yaml
path, commit = sys.argv[1], sys.argv[2]
raw = open(path, 'rb').read()
y = yaml.safe_load(raw)
out = {
  "schema": "humanaios.resource-units.snapshot.v1",
  "source": "operations/RESOURCE_UNITS.yaml", "source_commit": commit, "source_sha256": hashlib.sha256(raw).hexdigest(),
  "status": y.get("status"), "ratification_hash": y.get("ratification_hash"),
  "policy": {"conversion": y["policy"]["conversion"], "shadow_price_min_n": y["policy"]["shadow_price_min_n"]},
  "dimensions": sorted(y["dimensions"].keys()),
  "units": [{"symbol": u["symbol"], "status": u.get("status"), "dimension": u["dimension"], "kind": u.get("kind"),
             "sign": u.get("sign"), "conservation": u.get("conservation")} for u in y["units"]],
}
print(json.dumps(out, indent=2, sort_keys=True))

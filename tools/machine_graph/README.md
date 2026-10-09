# Machine Substrate Graph collector

Issue: #596

This prototype builds a local, metadata-first graph of what a macOS machine can actually provide to HumanAIOS.

## Design boundary

The collector does **not** read user document contents.

It records:
- host/OS/resource metadata;
- mounted volume capacity;
- application bundle metadata;
- selected executable/runtime availability;
- current execution context;
- user LaunchAgent artifact filenames and correlated loaded state;
- explicitly selected local Git repositories;
- explicitly selected Python virtual environments;
- omission states and provenance.

It deliberately does **not** record:
- serial number;
- MAC addresses;
- hostname;
- browser credential stores;
- Keychain contents;
- SSH/private keys;
- document contents;
- Git remote URLs.

## Run on the current test Mac

From the local clone of the branch containing this collector:

```bash
cd "$HOME/HumanAIOS-machine-scan/operations-pr594"

git fetch origin feat/596-local-machine-substrate-graph
git checkout -B feat/596-local-machine-substrate-graph origin/feat/596-local-machine-substrate-graph

python3 tools/machine_graph/collect_macos.py \
  --root "$HOME/HumanAIOS-machine-scan" \
  --venv "$HOME/HumanAIOS-machine-scan/shacl-test/venv" \
  --output "$HOME/HumanAIOS-machine-scan/machine-graph/machine-substrate.json"

python3 tools/machine_graph/validate_snapshot.py \
  "$HOME/HumanAIOS-machine-scan/machine-graph/machine-substrate.json"
```

Expected final line:

```text
validation=PASS
```

## Observation semantics

`OBSERVED_UNAVAILABLE` means the collector actually checked the bounded target and did not find usable capability.

`NOT_SCANNED` means the collector intentionally did not inspect that scope.

`PERMISSION_DENIED` means the target may exist, but this run could not observe it.

`UNKNOWN` means the observation did not support a stronger conclusion.

Absence outside an observed scope must never be interpreted as nonexistence.

## Current prototype limitations

- macOS only;
- application inventory covers /Applications and ~/Applications;
- repository discovery is opt-in and metadata-only;
- launch-agent correlation uses filename-derived labels and `launchctl list`; it does not parse plist contents;
- software capability inference is intentionally conservative;
- graph persistence is JSON nodes/edges for the prototype; RDF/PROV-O projection is a later stage.

## Next test

Use the resulting graph to answer a bounded attractor question from local evidence:

> Can this machine execute the canonical HumanAIOS SHACL validation, and what exact execution context satisfies it?

The answer should be derived from the machine graph rather than from conversational memory.

## Capability query

After producing and validating a snapshot, evaluate the first bounded local capability directly from machine evidence:

```bash
python3 tools/machine_graph/evaluate_capability.py \
  --graph "$HOME/HumanAIOS-machine-scan/machine-graph/machine-substrate.json" \
  --validation-receipt "$HOME/HumanAIOS-machine-scan/canonical-shacl-validation.txt" \
  --output "$HOME/HumanAIOS-machine-scan/machine-graph/capability-shacl.json"
```

A fully evidenced result should report:

```json
{
  "capability": "canonical-shacl-validation",
  "state": "SATISFIED",
  "authorization": "NONE",
  "can_authorize_external_action": false
}
```

This query is intentionally capability-only. `SATISFIED` means the graph contains an observed PySHACL runtime, an observed local operations repository, and a canonical validation receipt whose required PASS markers are present. It does not authorize any follow-on action.

Run the unit tests with:

```bash
python3 -m unittest tests/machine_graph/test_capability_query.py
```


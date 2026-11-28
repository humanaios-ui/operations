# Planning combination v1: local validation evidence

Base: `fab7ac329ebd6abc5d4d0d28af7bbfbe53b2f779`. Date: November 3, 2026.
This is local execution evidence, not protected CI, admission, ratification,
deployment, resource acquisition or independently verified human benefit.

## Environment and commands

Windows; bundled CPython 3.12 executable:
`C:/Users/truuz/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
Bundled Node executable:
`C:/Users/truuz/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`.
Below, `$py` and `$node` stand for those exact absolute executables.
From `humanaios-funding-pipeline/resource-miner`, PowerShell:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Get-Location).Path
$env:TMP=$env:TEMP
$env:PYTHONPATH='C:\Users\truuz\Downloads\operations-c78146a1a486dce1b2564a2902325ce8f4ba0683\planning-contract-test-deps'
& $py -B -m unittest discover -s tests -p 'test_planning*.py' -v
& $py -B -m unittest discover -s tests -p test_quiet_infrastructure_plan.py -v
& $py -B -m unittest discover -s tests -p test_witness_plan_projection.py -v
& $py -B -m resource_miner.cli --help
& $py -B -m resource_miner.on_track_reflex --smoke-test
& $py -B -m resource_miner.on_track_execution --smoke-test
& $py -B -m resource_miner.on_track_progress --smoke-test
& $node --test tests/test_on_track_browser.cjs
& $node --test tests/test_intent_feedback_browser.cjs
```

`jsonschema==4.26.0` and `PyYAML==6.0.3` were installed with pip `--target`
into that isolated directory OUTSIDE the repository. No production dependency
or requirements file changes. Before installing jsonschema, structural schema
checks skipped explicitly (38 tests, one class skip); final run executed them.
Initial document validation was blocked by missing PyYAML; final validation ran.

## Results

- New combination-contract tests: 26 passed, zero failures/errors/skips.
- Focused planning total: 40 passed, zero failures/errors/skips.
- Existing quiet-infrastructure integration: 7 passed.
- Existing Witness plan projection integration: 10 passed.
- Existing CLI integration: two synthetic file round trips (resolve/export),
  executed inside the new unittest suite, pass without changing fixture files.
- Three existing On-Track smoke checks: PASS each; not production HTTP probes.
- Node On-Track browser: 6 passed, zero failures/skips.
- Node feedback browser (the Resource Miner PR workflow check): 8 passed,
  zero failures/skips. The historical four Windows CRLF matcher failures do not
  reproduce on current main; no browser tests or HTML were changed.
- `git diff --check`: PASS.
- Repository root `python -B tools/repo_health.py --strict`: PASS, 100/100.
- Root `python -B .doc-control/validate.py`: PASS, 50 registered documents,
  no violations, 31 pre-existing advisory warnings.
- Root `python -B .doc-control/render.py --check`: PASS, registry output in sync.

## Full Resource Miner baseline versus patch

The first unchanged baseline used ordinary discovery:
`python -B -m unittest discover -s tests -v` (TEMP/TMP as above).
612 tests; four failures, 18 error records (including subtests), nine skips.
Most errors were sandbox-denied loopback sockets (WinError 10013), so they were
not suppressed: both original and changed code were compared with socket access.

The comparison runner (below) used `python -B -` and the identical environment.
For baseline, `$env:PLANNING_BASELINE='1'`: load original planning.py from HEAD in
memory and exclude ONLY the new test module. No tracked file is swapped/edited.
For post-change, `$env:PLANNING_BASELINE='0'`: execute current code and every test.
The code loads the same test_*.py modules as Resource Miner unittest discovery.
It also counts successful test methods explicitly (subtests are not extra tests).

| Run | Executed | Passed | Failed | Errored | Skipped |
|---|---:|---:|---:|---:|---:|
| Original HEAD planning code | 612 | 597 | 4 | 2 | 9 |
| Patched planning code | 638 | 623 | 4 | 2 | 9 |

Failure/error identities matched exactly. Nine skips are the existing
`test_feedback_replay_1002` historical pinned E1 cases, which require explicit
isolated CI. No unrelated test or fixture was edited. The environment is NOT
entirely green. The six unsuccessful tests are existing ACAT-R verification/source
readback behavior; their root cause was not repaired or promoted to certainty.

```
ERROR: test_p1_four_conditions_have_explicit_machine_readable_states (test_acat_r_verification_bridge.ResourceMinerFourStateExperiment.test_p1_four_conditions_have_explicit_machine_readable_states)
ERROR: test_unavailable_source_not_equated_with_closed_opportunity (test_acat_r_verification_bridge.ResourceMinerFourStateExperiment.test_unavailable_source_not_equated_with_closed_opportunity)
FAIL: test_live_http_reuses_actual_curated_hold_when_external_dev_adapter_fails (test_acat_r_live_source_readback.ActualSourceTransitionTests.test_live_http_reuses_actual_curated_hold_when_external_dev_adapter_fails)
FAIL: test_previous_human_recheck_remains_unknown_and_is_not_job_closure (test_acat_r_live_source_readback.ActualSourceTransitionTests.test_previous_human_recheck_remains_unknown_and_is_not_job_closure)
FAIL: test_snapshot_http_projects_real_change_instead_of_old_active_status (test_acat_r_live_source_readback.ActualSourceTransitionTests.test_snapshot_http_projects_real_change_instead_of_old_active_status)
FAIL: test_p3_replayed_snapshot_does_not_erase_newer_source_holds (test_acat_r_verification_bridge.ResourceMinerFourStateExperiment.test_p3_replayed_snapshot_does_not_erase_newer_source_holds)
```

Preserved terminal exceptions: `KeyError: ACATR-CONFLICTING`, `StopIteration`,
three missing-case `AssertionError: 0 != 1`, and ACATR-CONFLICTING unexpectedly
present in source holds. The same failures occur with original planning code.

## Coordinator and repository dependencies

No policy/state/graph/workflow changes. Current main Coordinator code read the
public state branch at `08dcd89de03e49ab8c59d9f17fe2fa8a2625f1d4` in memory:
`state.parse_ledger(ledger)` then `state.replay_events(events, ledger_text=ledger)`.
Result: `EVENTS 169 PROJECTION_MATCH True`. The historical event-26 replay error
does not reproduce at these pins. Chain/projection equality is not independent
actor authentication or admission for this work. Draft #909 and #943 are untouched.
Draft #914 independently touches planning.py for a three-source context pilot;
it is not a dependency, but overlapping-file merge conflicts need review.
The new combination policy has not been found ratified in the inspected
GOVERNANCE/REGISTERED contracts; this patch remains a proposed opt-in contract.

## Full-suite runner

```python
import os,sys,subprocess,unittest
from pathlib import Path
baseline=os.environ.get("PLANNING_BASELINE")=="1"
if baseline:
 import resource_miner.planning as planning
 source=subprocess.check_output(["git","show","HEAD:humanaios-funding-pipeline/resource-miner/resource_miner/planning.py"]).decode("utf-8")
 for name in list(vars(planning)):
  if not name.startswith("__"): delattr(planning,name)
 exec(compile(source,planning.__file__,"exec"),vars(planning))
sys.path.insert(0,str(Path("tests").resolve()))
suite=unittest.TestSuite()
for path in sorted(Path("tests").glob("test_*.py")):
 if baseline and path.name=="test_planning_combination.py": continue
 suite.addTests(unittest.defaultTestLoader.loadTestsFromName(path.stem))
class Counted(unittest.TextTestResult):
 successes=0
 def addSuccess(self,test):
  self.successes+=1
  super().addSuccess(test)
r=unittest.TextTestRunner(verbosity=2,resultclass=Counted).run(suite)
print("COUNTS",r.testsRun,"PASS",r.successes,"FAIL",len(r.failures),"ERROR",len(r.errors),"SKIP",len(r.skipped),flush=True)
sys.exit(not r.wasSuccessful())
```

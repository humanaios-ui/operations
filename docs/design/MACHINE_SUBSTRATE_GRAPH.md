# Machine Substrate Graph

Status: PROVISIONAL IMPLEMENTATION  
Issue: #596

## Purpose

Represent the locally observable machine substrate as evidence-bearing nodes and edges so HumanAIOS can ask **what capability is actually available here?** before defaulting to external research or installation.

## Core model

```text
Machine
 ├─ HAS_EXECUTION_CONTEXT -> ExecutionContext
 ├─ HAS_VOLUME -> Volume
 ├─ HAS_SOFTWARE -> SoftwareAsset
 ├─ HAS_TOOL -> Tool
 ├─ HAS_RUNTIME -> PythonEnvironment / Runtime
 ├─ HAS_REPOSITORY -> LocalRepository
 ├─ HAS_LAUNCH_ARTIFACT -> LaunchAgentArtifact
 └─ HAS_LOADED_SERVICE -> LoadedService
```

A later capability layer can derive bounded claims such as:

```text
Capability("canonical SHACL validation")
  REQUIRES Tool/PythonEnvironment
  REQUIRES repository graph/shapes/fixtures
  REQUIRES execution context
  EVIDENCED_BY validation receipt
```

## Critical finding from the first local experiment

Installed software is not equivalent to executable capability.

The local PySHACL experiment produced:

```text
Attempt 1:
  PySHACL installed
  fresh shell did not expose venv python
  validator = UNEXECUTED

Attempt 2:
  same installed PySHACL
  venv interpreter addressed explicitly
  validator exit code = 0
  canonical fixtures = PASS
```

Therefore `ExecutionContext` is first-class. Capability observations may depend on:
- interpreter path;
- virtual environment;
- PATH;
- shell/session;
- current working directory;
- permissions.

## Observation-state invariant

The graph separates:
- `OBSERVED_AVAILABLE`
- `OBSERVED_UNAVAILABLE`
- `NOT_SCANNED`
- `PERMISSION_DENIED`
- `UNKNOWN`
- `STALE_OBSERVATION`

This preserves the open-world boundary: not observed != false.

## Privacy boundary

The first collector is metadata-first.

By default it does not collect hostnames, serial numbers, MAC addresses, document contents, browser credentials, Keychain contents, SSH/private keys, or Git remote URLs.

Repository discovery occurs only below roots explicitly supplied by the user.

## Attractor integration

The Machine Substrate Graph becomes the first search field for capability/dependency attractors:

```text
Dependency / capability need
        ↓
local machine attractor
        ↓
Machine Substrate Graph
        ↓
SATISFIED locally?
   /             \
 yes              no/unknown
  ↓                   ↓
execute         external attractor
                or user authorization
```

Local evidence should reduce unnecessary installation, web retrieval, and speculative assumptions.

## Compression

Human-facing summaries such as `Python available` are projections, not canonical evidence. They must remain expandable to:
- exact executable path;
- version;
- environment;
- observation time;
- execution context;
- supporting receipt.

## Initial promotion test

The prototype is promotable only if it can:
1. run without reading unrelated personal content;
2. distinguish not-scanned from not-found;
3. represent installed-vs-executable context;
4. validate its own node/edge integrity;
5. answer the canonical SHACL capability question from local observations.

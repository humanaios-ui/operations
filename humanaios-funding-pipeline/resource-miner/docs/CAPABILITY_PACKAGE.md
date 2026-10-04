# CPK Capability Package

Issue #715 introduces `CPK-*`, a many-requirement × many-resource composition primitive.

## Canonical progression

```text
DMD-* Demand Profile
  ↓
DMR-* semantic requirements
  ↓
BRQ-* brokerable requirements
  ↓
BSA-* suitability assessments
  ↓
CPK-* Capability Package
  ↓
package-level composition screen
  ↓
authorization remains separate
```

## Purpose

A CPK answers:

> Does this specific composition of resources adequately cover the brokerable demand, what remains unresolved, and does composition introduce new control risk?

It does not authorize execution.

## Exact lineage

Each package binding preserves:

```text
DMR-* demand requirement
→ BRQ-* broker requirement
→ BSA-* selected suitability assessment(s)
→ RES-* selected resource(s)
```

A CPK refuses:

- BRQ records without exact DMR lineage;
- BRQ/DMR mode mismatch;
- BRQ/DMR semantic-class mismatch;
- selected BSA records for another opportunity;
- stale BSA resource digests;
- stale BSA resource-screen lineage;
- missing selected resources.

No label-only reconstruction is used.

## Coverage semantics

A requirement binding can be:

```text
ADEQUATE
PARTIAL
UNKNOWN
UNRESOLVED
```

For package-level hard coverage:

```text
REQUIRED + ADEQUATE
→ covered

REQUIRED + PARTIAL/UNKNOWN/UNRESOLVED
→ required coverage incomplete

OPTIONAL/PREFERRED/CONDITIONAL/SCORED gap
→ retained as nonrequired gap
→ does not by itself fail required coverage
```

Therefore:

```text
OPTIONAL_GAP != REQUIRED_GAP
COVERAGE_COMPLETE != AUTHORIZATION
```

## Composition screen

Resource-level screening is not sufficient.

```text
RESOURCE_A_SAFE
+
RESOURCE_B_SAFE
!=
PACKAGE_SAFE
```

The CPK screen considers:

- required capability coverage;
- resource provenance;
- license state;
- local permission requirements;
- network behavior;
- credential requirements;
- external state-change capability;
- auditability;
- least-privilege compatibility;
- declared resource conflicts;
- cross-resource credential propagation.

States:

```text
PASS
PASS_WITH_CONDITIONS
FAIL
UNKNOWN
```

Examples:

- two individually PASS resources with a declared incompatibility → package FAIL;
- a multi-resource package containing a credential-requiring component → credential-propagation review condition;
- an uncovered REQUIRED requirement → package FAIL;
- an uncovered OPTIONAL requirement → recorded gap, not required-coverage failure.

## Service Surface Taxonomy

The user-supplied service concepts map cleanly as descriptive service-surface classes.

### 1. NETWORK_TRANSPORT

Examples include HTTP/HTTPS, alternate HTTP ports, WebSocket transport, HTTP/2, HTTP/3/QUIC, gRPC transport, SSH/FTP/SMTP, database listeners, and container/orchestration APIs.

### 2. WEB_APPLICATION

Examples include static assets, authentication flows, search/filter/pagination, forms, file-transfer workflows, admin/dashboard/CMS interfaces, status/health/metrics routes, and debug/configuration exposure routes.

### 3. API_SERVICE

Examples include REST, GraphQL, SOAP/WSDL, JSON-RPC/XML-RPC, gRPC-Web, webhook test surfaces, OpenAPI/Swagger, Postman collections, and GraphiQL.

### 4. REALTIME_EVENT

Examples include WebSocket, Server-Sent Events, long polling, Socket.IO, SignalR, and MQTT over WebSocket.

### 5. AUTH_IDENTITY

Examples include OAuth, OpenID Connect, OIDC discovery, authorization/token/userinfo services, SAML metadata, JWT/JWKS, sessions, CSRF, and MFA workflows.

### 6. DISCOVERY_METADATA

Examples include robots.txt, sitemap.xml, security.txt, humans.txt, manifest.json, service workers, `.well-known` resources, favicon, cross-domain policy files, ads.txt, and app-ads.txt.

### 7. CLIENT_BROWSER

Examples include JavaScript/source maps, browser-visible configuration/endpoints, hidden fields/comments, cookies and browser storage, Workers/WebAssembly, iframes/postMessage, and permission-gated browser APIs.

### 8. STORAGE_CLOUD

Examples include object storage, Azure Blob Storage, Google Cloud Storage, CDNs, and database/object-store service endpoints.

### 9. ADMIN_OPS_MANAGEMENT

Examples include CI/CD runners, Kubernetes/Docker management APIs, Prometheus/Grafana/Kibana, database admin tools, and logs/metrics/tracing surfaces.

### 10. THIRD_PARTY_EMBEDDED

Examples include analytics, advertising, CDNs, social widgets, payment gateways, support/chat widgets, maps, fonts, and embedded video.

These are classification descriptors only.

```text
SERVICE_SURFACE_CLASSIFICATION != TARGET_SCOPE
TARGET_SCOPE != METHOD_PERMISSION
METHOD_PERMISSION != AUTHORIZATION
```

A CPK therefore always records:

```text
target_scope_state = NOT_ESTABLISHED
method_permission_state = NOT_ESTABLISHED
authorization_state = NOT_REQUESTED
authority_effect = NONE
```



## Operational modes and interaction classes

A resource project and a resource operational mode are not the same evidence object.

Examples:

```text
Amass / PASSIVE
!=
Amass / ACTIVE

Shodan / INDEX_QUERY
!=
Shodan / SCAN_REQUEST

Censys / INDEX_QUERY
!=
Censys / LIVE_RESCAN
```

Resource Miner therefore supports mode-bound resource variants. The operational mode contributes to the canonical resource representation and produces a distinct `RES-*` identity.

Canonical resource composition fields include:

```text
operational_mode
service_surface_classes
composition_conflicts
```

These fields participate in `ResourceCandidate.to_dict()` and therefore in the BSA resource digest used by CPK freshness checks.

The interaction vocabulary distinguishes:

```text
NONE
PASSIVE_PUBLIC_SOURCE
THIRD_PARTY_API_READ_ONLY
TARGET_READ_ONLY
TARGET_ACTIVE
MIXED
UNKNOWN
```

Legacy `READ_ONLY` and `ACTIVE` remain accepted for compatibility.

This distinction prevents index-query services from being mislabeled as target-touching:

```text
Shodan/Censys indexed search
→ THIRD_PARTY_API_READ_ONLY

direct target interaction
→ TARGET_READ_ONLY | TARGET_ACTIVE
```

Credentials, licensing/terms, network behavior, and external-state-change capability remain separate screening dimensions.

A demand profile may also constrain `allowed_network_behaviors`. A capability-complete package still fails the package screen when a selected operational mode violates that interaction policy.

```text
CAPABILITY_COMPLETE
!=
INTERACTION_POLICY_COMPLIANT
```

## Verified candidate profiles

The regression corpus includes descriptive, non-executing profiles for:

- Subfinder passive discovery;
- OWASP Amass passive and active variants;
- Shodan indexed search;
- Censys indexed search;
- Assetnote continuous attack-surface management.

These fixtures validate metadata, surface classification, interaction class, credentials/terms conditions, and mode separation only. They do not authorize or execute the tools.

## Integrity

`CPK-*` identity is derived from the selected bindings/resources/suitability records/service-surface classes.

`package_sha256` covers the complete public package state except the hash field itself.

Deserialization rejects mutation.

## Non-goals

CPK does not:

- discover targets;
- establish security-program scope;
- authorize methods;
- run scanners or tools;
- install resources;
- submit findings;
- create application/bid/submission authority;
- infer eligibility;
- grant future authority based on package completeness.

A future authorization layer may consume CPK as evidence, but must separately establish scope, method permission, consequence ceiling, and human/governance authority.

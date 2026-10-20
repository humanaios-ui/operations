# HumanAIOS Resource System — local prototype v0.1

This dedicated project **composes** Resource Miner and Entitlement Navigator through
their existing handoff functions. Neither dependency is moved or modified. Need
alignment remains a discovery signal, never eligibility or a recommendation.

## Milestone boundary

This change is a bounded **prototype v0.1 milestone for issue #588**, not completion
of that issue. The runtime is caller-driven and explicit-tick only: it does not run
a background scanner, monitor sources, deploy a service, or perform external actions.
Issue #588 must remain open for the persistent runtime, authenticated inputs,
production storage, integration, and exact-head admission work.

Run from the source checkout with Python 3.10 or later; no network or third-party
runtime/test dependencies are needed:

```sh
cd humanaios-resource-system
python3 -m unittest discover -s tests -v
```

The package groups controller, manager, runtime and adapters under
`resource_system/` to keep imports isolated. JSON schemas and UI contracts remain
at the project root. Source-checkout execution is supported; packaging these
schema files for a standalone wheel is deferred.

See [project boundaries](docs/PROJECT_SPEC.md), [privacy](docs/ONBOARDING_AND_PII.md)
and [UI contracts](docs/UI_UX_CONTRACT.md). Tests use synthetic RM-002 requirements
and Azure credit records; they do not verify any person's eligibility, actual
application, credit ownership or expiration date.

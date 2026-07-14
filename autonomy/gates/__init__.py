"""
autonomy.gates — executable Zone (Z1/Z2/Z3) gating framework.

This package is the HumanAIOS/ACAT governance-gate stack: the executable
form of the autonomy / ECO gating model (propose != ratify, no self-execution,
operator decides). It is a self-contained bundle — every module master_gateway
wires is co-located so the framework imports and runs without external path
setup.

See README.md for architecture, the known registry gap, and the security
seams that keep this library-only (no automated execution wiring).

Provenance: HumanAIOS/ACAT program, sessions S-0711/0713-26 (grok-assisted).
Landed in operations via the docs/_inbox_ integration, S-071426.
"""

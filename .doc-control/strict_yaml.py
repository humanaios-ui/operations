#!/usr/bin/env python3
"""A YAML loader that refuses duplicate mapping keys, for registry consumers.

`yaml.safe_load` silently keeps the LAST of a repeated key. That is the defect
that left `z2_ratification_gate.yml` dead for 122 runs, and a review round found
it again in the document-control tools: appending a second `review_baseline: {}`
to `document-registry.yaml` made both blocking checks read an empty mapping and
pass, reopening the very bypass the baseline was added to close.

A single line of YAML can therefore disable a gate with no error anywhere. Every
tool that reads a controlled registry must parse it strictly, so this lives in
one module rather than being re-implemented per tool — the first version of the
fix hardened `z1-inbox/INDEX.yaml` alone and left its sibling registry open.

Usage:
    from strict_yaml import load_registry
    reg = load_registry(path)      # raises yaml.YAMLError on a duplicate key

Deps: PyYAML. No network, no writes.
"""
from __future__ import annotations

import sys

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

__all__ = ["StrictLoader", "load_registry", "loads"]


class StrictLoader(yaml.SafeLoader):
    """SafeLoader that raises on a duplicate mapping key instead of overwriting."""


def _no_duplicates(loader: yaml.Loader, node: yaml.MappingNode, deep: bool = False) -> dict:
    out: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in out:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate key {key!r}", key_node.start_mark)
        out[key] = loader.construct_object(value_node, deep=deep)
    return out


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


def loads(text: str) -> dict:
    """Parse YAML text strictly. Raises yaml.YAMLError on a duplicate key."""
    return yaml.load(text, StrictLoader) or {}


def load_registry(path: str) -> dict:
    """Parse a registry file strictly. Raises yaml.YAMLError on a duplicate key."""
    with open(path, encoding="utf-8") as fh:
        return yaml.load(fh, StrictLoader) or {}


def run_smoke_test() -> int:
    dup = "review_baseline:\n  A: \"2026-08-01\"\nreview_baseline: {}\n"
    assert yaml.safe_load(dup)["review_baseline"] == {}, \
        "safe_load no longer silently takes the last duplicate; revisit this module"
    try:
        loads(dup)
        raise AssertionError("StrictLoader accepted a duplicate key")
    except yaml.YAMLError as exc:
        assert "duplicate key" in str(exc), exc
    # Nested duplicates must be caught too, not just top-level ones.
    try:
        loads("review_policy:\n  review: 90\n  review: 1\n")
        raise AssertionError("StrictLoader accepted a nested duplicate key")
    except yaml.YAMLError as exc:
        assert "duplicate key" in str(exc), exc
    assert loads("a: 1\nb: {c: 2}\n") == {"a": 1, "b": {"c": 2}}
    assert loads("") == {}
    print("smoke-test OK — rejects top-level and nested duplicate keys; "
          "safe_load's silent-overwrite behaviour is asserted so the test cannot rot.")
    return 0


if __name__ == "__main__":
    sys.exit(run_smoke_test())

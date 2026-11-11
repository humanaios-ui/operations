"""HumanAIOS Builder v1.7 compliant: read-only Azure inventory projection (#915)."""
TOOL_NAME = "azure_readiness"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1
TOOL_SESSION = "S-20261017-AZURE-915"

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


FAMILIES = {
    "microsoft.containerregistry/registries": "REGISTRY",
    "microsoft.app/containerapps": "APP_HOSTING",
    "microsoft.app/jobs": "APP_HOSTING",
    "microsoft.compute/virtualmachines": "VM",
    "microsoft.dbforpostgresql/flexibleservers": "POSTGRESQL",
    "microsoft.search/searchservices": "SEARCH",
    "microsoft.cognitiveservices/accounts": "AI_SERVICES",
}
SAFE_TOKEN = re.compile(r"[A-Za-z0-9_. /-]{1,100}\Z")


def safe_token(value):
    return value if isinstance(value, str) and SAFE_TOKEN.fullmatch(value) else "UNKNOWN"


def project(resources, observed_at):
    """Project allowlisted fields while omitting names, URLs, tags and properties."""
    if not isinstance(resources, list):
        raise ValueError("Inventory must be a JSON resource list")
    rows = []
    seen = set()
    for resource in resources:
        if not isinstance(resource, dict):
            raise ValueError("Resource must be an object")
        resource_id = resource.get("id")
        if not isinstance(resource_id, str) or not resource_id.startswith("/subscriptions/"):
            raise ValueError("Resource requires an Azure resource ID")
        identity = resource_id.lower().rstrip("/")
        if identity in seen:
            raise ValueError("Duplicate resource ID")
        seen.add(identity)
        kind = resource.get("type")
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError("Resource requires a type")
        kind = kind.lower()
        if kind not in FAMILIES:
            family = "OTHER"
        else:
            family = FAMILIES[kind]
        sku = resource.get("sku") or {}
        if not isinstance(sku, dict):
            raise ValueError("Resource SKU must be an object")
        rows.append({
            "resource_ref": hashlib.sha256(identity.encode()).hexdigest(),
            "family": family,
            "resource_type": safe_token(kind),
            "sku_name": safe_token(sku.get("name")),
            "sku_tier": safe_token(sku.get("tier")),
            "deployment_revision": "UNKNOWN",
            "backend_state": "UNKNOWN",
            "readiness": "NEEDS_EVIDENCE",
            "missing_evidence": ["deployed_revision", "functional_smoke_receipt",
                                 "real_backend_readiness", "daily_billing_evidence"],
        })
    rows.sort(key=lambda row: row["resource_ref"])
    return {
        "schema": "azure_readiness_v1",
        "report_generated_at": observed_at,
        "authority_effect": "NONE",
        "qualification": "UNVERIFIED",
        "billing_state": "UNKNOWN",
        "qualifying_day_count": None,
        "resource_count": len(rows),
        "candidate_service_families": sorted({r["family"] for r in rows} - {"OTHER"}),
        "resources": rows,
    }


def collect(subscription):
    """Only Azure command used: resource list. No account switching or mutations."""
    if not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", subscription):
        raise ValueError("Expected a subscription UUID")
    result = subprocess.run(
        ["az", "resource", "list", "--subscription", subscription,
         "--output", "json", "--only-show-errors"],
        capture_output=True, text=True, timeout=120, check=False,
    )
    if result.returncode:
        # CLI errors can contain private account/resource details.
        raise ValueError("Azure inventory failed; check local Azure access privately")
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--inventory", "--input", dest="inventory", type=Path,
                        help="Private az resource list JSON")
    source.add_argument("--subscription", help="Collect using read-only Azure CLI")
    source.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        assert project([], "test")["qualifying_day_count"] is None
        print("smoke-test OK")
        return
    try:
        raw = (json.loads(args.inventory.read_text()) if args.inventory
               else collect(args.subscription))
        report = project(raw, datetime.now(timezone.utc).isoformat())
        report["inventory_observed_at"] = ("UNKNOWN" if args.inventory
                                             else report["report_generated_at"])
    except (ValueError, OSError, subprocess.TimeoutExpired):
        parser.exit(2, "Inventory unavailable or invalid; no readiness report produced.\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

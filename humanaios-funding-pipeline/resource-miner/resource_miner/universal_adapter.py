"""Universal Resource Adapter: protocol and passive registry, no executor.

Registry entries declare bounded public observation support. All submitted
records are supplied by callers; this module makes zero network requests.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from urllib.parse import urlsplit


class AdapterDenied(ValueError):
    """An asserted source, policy, or action cannot pass the passive boundary."""


@dataclass(frozen=True)
class ProviderManifest:
    provider_id: str
    version: str
    hosts: tuple[str, ...]
    categories: tuple[str, ...]
    public_paths: tuple[str, ...]
    source_class: str = "PUBLIC_METADATA"
    adapter_mode: str = "PASSIVE_ONLY"
    authority_effect: str = "NONE"


@dataclass(frozen=True)
class Observation:
    provider_id: str
    external_id: str
    title: str
    source_url: str
    category: str
    observed_at: str
    evidence_digest: str
    source_class: str = "PUBLIC_METADATA"


def _url_allowed(url: str, manifest: ProviderManifest) -> bool:
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and p.hostname in manifest.hosts
                and p.path in manifest.public_paths and not p.username
                and not p.password and p.port is None and not p.query
                and not p.fragment)
    except ValueError:
        return False


class AdapterRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderManifest] = {}

    def register(self, manifest: ProviderManifest) -> None:
        if (not manifest.provider_id or manifest.provider_id in self._providers
                or manifest.adapter_mode != "PASSIVE_ONLY"
                or manifest.authority_effect != "NONE"
                or manifest.source_class != "PUBLIC_METADATA"
                or not manifest.version or not manifest.hosts or not manifest.categories
                or not manifest.public_paths):
            raise AdapterDenied("invalid or self-authorizing provider manifest")
        if any(not host or host != host.lower() or "://" in host
               or "/" in host or "*" in host or host.startswith(".")
               for host in manifest.hosts):
            raise AdapterDenied("host scope must be exact")
        if any(not path.startswith("/") or "?" in path or "#" in path or "*" in path
               for path in manifest.public_paths):
            raise AdapterDenied("path scope must be exact")
        self._providers[manifest.provider_id] = manifest

    def normalize(self, observation: Observation) -> dict:
        manifest = self._providers.get(observation.provider_id)
        if manifest is None:
            raise AdapterDenied("provider unregistered")
        if (observation.source_class != "PUBLIC_METADATA"
                or observation.category not in manifest.categories
                or not _url_allowed(observation.source_url, manifest)
                or not observation.external_id or not observation.title
                or not observation.observed_at or not observation.evidence_digest
                or len(observation.evidence_digest) != 64
                or any(c not in "0123456789abcdef" for c in observation.evidence_digest)):
            raise AdapterDenied("unsupported observation provenance or scope")
        stable_id = sha256(
            (observation.provider_id + "\0" + observation.external_id).encode()
        ).hexdigest()[:24]
        return {
            "resource_id": "URA-" + stable_id,
            "title": observation.title,
            "source_name": manifest.provider_id,
            "source_url": observation.source_url,
            "canonical_url": observation.source_url,
            "discovery_method": "supplied_public_metadata",
            "discovered_at": observation.observed_at,
            "resource_types": [observation.category],
            "primary_source_url": observation.source_url,
            "evidence": [{
                "url": observation.source_url, "kind": "PUBLIC_METADATA",
                "observed_at": observation.observed_at,
                "claim": "digest:sha256:" + observation.evidence_digest,
            }],
            "status": "UNKNOWN",
            "eligibility_status": "UNASSESSED",
            "route": "VERIFY_NOW",
            "authority_effect": "NONE",
            "authorization": "NOT_GRANTED",
            "execution": "NOT_AVAILABLE",
            "provider_version": manifest.version,
        }

    def request_action(self, provider_id: str, action: str, receipt: object = None) -> None:
        # No execution API is implemented. Supplying a receipt cannot enable one.
        raise AdapterDenied("URA has no action authority or executor")

    def providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))


def synthetic_reference_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    for manifest in (
        ProviderManifest("GITHUB_PUBLIC", "0.1", ("github.com",),
                         ("OPEN_SOURCE_RESOURCE",), ("/humanaios-ui/operations",)),
        ProviderManifest("OUTLIER_PUBLIC", "0.1", ("outlier.ai",),
                         ("HUMAN_LABOR_INCOME_OPPORTUNITY", "HUMAN_NETWORK_REWARD",
                          "AI_EVALUATION_ENVIRONMENT"),
                         ("/faq", "/legal/terms-of-use")),
        ProviderManifest("TRIAL_SYNTHETIC", "0.1", ("example.org",),
                         ("AI_EVALUATION_ENVIRONMENT",), ("/synthetic-trial",)),
    ):
        registry.register(manifest)
    return registry

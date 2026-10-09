import unittest

from resource_miner.broker import screen_resource
from resource_miner.models import EvidenceRef, bind_resource_operational_mode
from resource_miner.normalize import normalize_generic


OBSERVED = "2026-10-04T16:10:00Z"


def candidate(
    *,
    title,
    url,
    source_category,
    surfaces,
    mode,
    evidence_claim,
):
    base = normalize_generic(
        title=title,
        url=url,
        source_name="verified-current-source",
        discovery_method="fixture",
        source_category=source_category,
        observed_at=OBSERVED,
    )
    base.service_surface_classes = list(surfaces)
    base.evidence = [
        EvidenceRef(
            url=url,
            kind="source",
            observed_at=OBSERVED,
            claim=evidence_claim,
        )
    ]
    return bind_resource_operational_mode(base, mode)


class CpkSecurityCandidateProfileTests(unittest.TestCase):
    def test_subfinder_passive_profile(self):
        resource = candidate(
            title="Subfinder",
            url="https://github.com/projectdiscovery/subfinder",
            source_category="open_source_tool",
            surfaces=["DISCOVERY_METADATA"],
            mode="PASSIVE",
            evidence_claim=(
                "ProjectDiscovery describes Subfinder as passive subdomain enumeration "
                "using passive online sources; provider APIs may optionally require keys."
            ),
        )
        screen = screen_resource(
            resource,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="PASSIVE_PUBLIC_SOURCE",
            credential_requirement="OPTIONAL",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        self.assertEqual(resource.service_surface_classes, ["DISCOVERY_METADATA"])
        self.assertEqual(resource.operational_mode, "PASSIVE")
        self.assertEqual(screen.state, "PASS")

    def test_amass_passive_and_active_are_distinct_resource_variants(self):
        base_url = "https://github.com/owasp-amass/amass"
        passive = candidate(
            title="OWASP Amass",
            url=base_url,
            source_category="open_source_tool",
            surfaces=["DISCOVERY_METADATA", "NETWORK_TRANSPORT"],
            mode="PASSIVE",
            evidence_claim=(
                "OWASP Amass performs attack-surface mapping and supports passive "
                "intelligence/DNS enumeration as well as active reconnaissance."
            ),
        )
        active = candidate(
            title="OWASP Amass",
            url=base_url,
            source_category="open_source_tool",
            surfaces=["DISCOVERY_METADATA", "NETWORK_TRANSPORT"],
            mode="ACTIVE",
            evidence_claim=(
                "OWASP Amass supports active reconnaissance, DNS resolution and "
                "brute-force enumeration modes in addition to passive operation."
            ),
        )
        self.assertNotEqual(passive.resource_id, active.resource_id)
        passive_screen = screen_resource(
            passive,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="PASSIVE_PUBLIC_SOURCE",
            credential_requirement="OPTIONAL",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        active_screen = screen_resource(
            active,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="TARGET_ACTIVE",
            credential_requirement="OPTIONAL",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        self.assertEqual(passive_screen.state, "PASS")
        self.assertEqual(active_screen.state, "PASS_WITH_CONDITIONS")

    def test_shodan_index_query_profile_is_not_target_touching(self):
        resource = candidate(
            title="Shodan Search API",
            url="https://developer.shodan.io/api",
            source_category="external_service",
            surfaces=[
                "NETWORK_TRANSPORT",
                "WEB_APPLICATION",
                "ADMIN_OPS_MANAGEMENT",
                "STORAGE_CLOUD",
            ],
            mode="INDEX_QUERY",
            evidence_claim=(
                "Shodan search/host APIs query Shodan's indexed host and service banner data; "
                "separate scan endpoints exist and are not represented by this mode."
            ),
        )
        screen = screen_resource(
            resource,
            provenance_state="VERIFIED",
            license_state="TERMS_REVIEW_REQUIRED",
            permissions_state="MINIMAL",
            network_behavior="THIRD_PARTY_API_READ_ONLY",
            credential_requirement="REQUIRED",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        self.assertEqual(screen.state, "PASS_WITH_CONDITIONS")
        self.assertFalse(
            any("TARGET_ACTIVE" in finding for finding in screen.findings)
        )

    def test_censys_index_query_profile_is_not_target_touching(self):
        resource = candidate(
            title="Censys Platform Search API",
            url="https://docs.censys.com/reference/get-started",
            source_category="external_service",
            surfaces=[
                "NETWORK_TRANSPORT",
                "WEB_APPLICATION",
                "ADMIN_OPS_MANAGEMENT",
                "STORAGE_CLOUD",
            ],
            mode="INDEX_QUERY",
            evidence_claim=(
                "Censys Platform API queries indexed host, web-property, certificate "
                "and service data; authenticated API access is plan/role dependent."
            ),
        )
        screen = screen_resource(
            resource,
            provenance_state="VERIFIED",
            license_state="TERMS_REVIEW_REQUIRED",
            permissions_state="MINIMAL",
            network_behavior="THIRD_PARTY_API_READ_ONLY",
            credential_requirement="REQUIRED",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        self.assertEqual(screen.state, "PASS_WITH_CONDITIONS")
        self.assertFalse(
            any("TARGET_ACTIVE" in finding for finding in screen.findings)
        )

    def test_assetnote_profile_is_commercial_and_target_touching_capable(self):
        resource = candidate(
            title="Assetnote Attack Surface Management",
            url="https://www.assetnote.io/resources/resources-overview",
            source_category="external_service",
            surfaces=[
                "DISCOVERY_METADATA",
                "NETWORK_TRANSPORT",
                "WEB_APPLICATION",
                "API_SERVICE",
            ],
            mode="CONTINUOUS_ASM",
            evidence_claim=(
                "Assetnote markets continuous asset discovery, exposure monitoring "
                "and external attack-surface scanning; it is now part of Searchlight Cyber."
            ),
        )
        screen = screen_resource(
            resource,
            provenance_state="VERIFIED",
            license_state="TERMS_REVIEW_REQUIRED",
            permissions_state="MINIMAL",
            network_behavior="TARGET_ACTIVE",
            credential_requirement="REQUIRED",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        self.assertEqual(screen.state, "PASS_WITH_CONDITIONS")
        self.assertIn("WEB_APPLICATION", resource.service_surface_classes)
        self.assertIn("API_SERVICE", resource.service_surface_classes)


if __name__ == "__main__":
    unittest.main()

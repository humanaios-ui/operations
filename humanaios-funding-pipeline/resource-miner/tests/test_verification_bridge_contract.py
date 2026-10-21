import unittest
from resource_miner.verification_bridge_contract import project, BridgeDenied
from resource_miner.universal_adapter import AdapterRegistry, ProviderManifest, Observation

def fixture():
    registry = AdapterRegistry()
    registry.register(ProviderManifest(
        "VERIFY_SYNTHETIC", "1", ("example.org",),
        ("INDEPENDENT_VERIFICATION_OPPORTUNITY",), ("/candidate",)))
    obs = Observation("VERIFY_SYNTHETIC", "claim-1", "Reproducibility challenge",
                      "https://example.org/candidate",
                      "INDEPENDENT_VERIFICATION_OPPORTUNITY",
                      "2026-10-09T18:00:00-05:00", "a" * 64)
    return registry, obs

class CrossContractTests(unittest.TestCase):
    def test_projection_invariants(self):
        reg, obs = fixture()
        row = project(reg, obs, need_state="EXPLICIT_VERIFICATION_REQUEST")
        self.assertFalse(row["resource"]["eligibility_assessed"])
        self.assertEqual(row["resource"]["route"], "WATCH")
        self.assertEqual(row["resource"]["eligibility_status"], "UNASSESSED")
        self.assertEqual(row["verification"]["screening_state"], "CANDIDATE")
        self.assertFalse(row["verification"]["can_authorize"])
        self.assertEqual(row["graph"]["authority_effect"], "NONE")
        self.assertEqual(row["resource"]["evidence"][0]["claim"], "digest:sha256:" + "a"*64)

    def test_unregistered_provider_denied(self):
        reg, obs = fixture()
        other = AdapterRegistry()
        with self.assertRaises(BridgeDenied):
            project(other, obs)

    def test_unregistered_path_denied(self):
        reg, obs = fixture()
        bad = Observation(obs.provider_id, obs.external_id, obs.title,
                          "https://example.org/private", obs.category,
                          obs.observed_at, obs.evidence_digest)
        with self.assertRaises(BridgeDenied):
            project(reg, bad)

    def test_bad_digest_denied(self):
        reg, obs = fixture()
        bad = Observation(obs.provider_id, obs.external_id, obs.title,
                          obs.source_url, obs.category, obs.observed_at, "invalid")
        with self.assertRaises(BridgeDenied):
            project(reg, bad)

    def test_cannot_supply_pretend_normalized_dict(self):
        reg, obs = fixture()
        with self.assertRaises(BridgeDenied):
            project(reg, reg.normalize(obs))

    def test_unregistered_category_denied(self):
        reg, obs = fixture()
        bad = Observation(obs.provider_id, obs.external_id, obs.title,
                          obs.source_url, "OPEN_SOURCE_RESOURCE",
                          obs.observed_at, obs.evidence_digest)
        with self.assertRaises(BridgeDenied):
            project(reg, bad)

    def test_claim_only_not_authority(self):
        reg, obs = fixture()
        row = project(reg, obs, need_state="CLAIM_ONLY")
        self.assertEqual(row["verification"]["screening_state"], "CLAIM_ONLY")
        self.assertFalse(row["can_authorize"])

if __name__ == "__main__":
    unittest.main()

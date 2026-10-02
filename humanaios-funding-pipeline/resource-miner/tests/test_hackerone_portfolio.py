import unittest

from resource_miner.security_capability import (
    OBSERVED_AVAILABLE,
    OBSERVED_UNAVAILABLE,
    UNKNOWN,
    profile_from_machine_graph,
    unknown_capability_profile,
)


class CapabilityProfileTests(unittest.TestCase):
    def test_machine_graph_evidence_is_not_assumed(self):
        graph = {
            "observed_at": "2026-10-02T19:00:00+00:00",
            "nodes": [
                {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "python3"}},
                {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "curl"}},
                {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "git"}},
                {"type": "Tool", "state": OBSERVED_UNAVAILABLE, "observed": {"name": "adb"}},
                {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "java"}},
            ],
            "omissions": [],
        }
        profile = profile_from_machine_graph(graph, source="fixture")
        self.assertEqual(profile.get("web_http_review").state, OBSERVED_AVAILABLE)
        self.assertEqual(profile.get("source_code_review").state, OBSERVED_AVAILABLE)
        self.assertEqual(profile.get("android_app_review").state, OBSERVED_UNAVAILABLE)
        self.assertEqual(profile.get("hardware_iot_review").state, UNKNOWN)

    def test_no_snapshot_means_unknown(self):
        profile = unknown_capability_profile()
        self.assertTrue(all(x.state == UNKNOWN for x in profile.capabilities.values()))


if __name__ == "__main__":
    unittest.main()

import copy
import unittest

from resource_miner.project_desk_bridge_e0 import BridgeInputError, propose_sync


def inputs():
    workspace = {"schema": "humanaios.workspace_view.v1", "revision": 2, "records": [
        {"id": "OPP-1", "title": "Contract pilot", "pursuit": "ACTIVE",
         "hold_reason": "HARDWARE", "tasks": [
            {"id": "TASK-1", "title": "Accept", "state": "DONE"},
            {"id": "TASK-2", "title": "Record", "state": "TODO"}]}]}
    desk = {"schema": "humanaios.project-desk.v1", "revision": 1,
            "projects": [], "tasks": [], "imports": []}
    return desk, workspace


class BridgeTest(unittest.TestCase):
    def test_source_ids_survive_without_false_completion(self):
        d, w = inputs()
        p = propose_sync(d, w)
        self.assertEqual(p["new_projects"][0]["proposed_id"], "OPP-1")
        self.assertEqual(p["new_tasks"][0]["proposed_id"], "TASK-1")
        self.assertEqual(p["new_tasks"][0]["proposed_status"], "TODO")
        self.assertEqual(p["new_tasks"][0]["source_reported_state"], "DONE")
        self.assertEqual(p["authority_effect"], "NONE")
        self.assertEqual((d, w), inputs())

    def test_exact_reimport_no_duplicates_and_local_ids_preserved(self):
        d, w = inputs()
        d["projects"].append({"id": "desk-project-existing", "name": "Contract pilot",
                              "origin": "INTENT-OS snapshot · OPP-1 · revision 1"})
        d["tasks"].append({"id": "desk-task-existing", "project": "desk-project-existing",
                           "status": "BLOCKED", "source": "OPP-1/TASK-1"})
        p = propose_sync(d, w)
        self.assertEqual(len(p["new_projects"]), 0)
        self.assertEqual(len(p["new_tasks"]), 1)
        self.assertEqual(p["linked_tasks"][0]["desk_task_id"], "desk-task-existing")
        self.assertEqual(p["linked_tasks"][0]["current_desk_status"], "BLOCKED")
        self.assertEqual(p, propose_sync(d, w))

    def test_stale_and_forked_revision_rejected(self):
        d, w = inputs()
        d["imports"].append({"id": "intent-workspace", "revision": 3, "data": w})
        with self.assertRaises(BridgeInputError):
            propose_sync(d, w)
        d["imports"][0]["revision"] = 2
        d["imports"][0]["data"] = {**w, "revision": 2, "records": []}
        with self.assertRaises(BridgeInputError):
            propose_sync(d, w)
        d["imports"][0]["data"] = copy.deepcopy(w)
        self.assertTrue(propose_sync(d, w)["requires_human_approval"])

    def test_mapped_project_origin_blocks_older_workspace_without_import(self):
        d, w = inputs()
        self.assertEqual(d["imports"], [])
        d["projects"].append({"id": "desk-existing", "name": "Contract pilot",
                              "origin": "INTENT-OS snapshot · OPP-1 · revision 3"})
        with self.assertRaisesRegex(BridgeInputError, "stale workspace revision"):
            propose_sync(d, w)
        w["revision"] = 3
        self.assertTrue(propose_sync(d, w)["requires_human_approval"])

    def test_malformed_project_origin_revision_rejected(self):
        for origin_revision in ("garbage", "-1", "02", "2 · injected", ""):
            with self.subTest(origin_revision=origin_revision):
                d, w = inputs()
                d["projects"].append({"id": "P", "name": "Contract pilot",
                                      "origin": "INTENT-OS snapshot · OPP-1 · revision " + origin_revision})
                with self.assertRaises(BridgeInputError):
                    propose_sync(d, w)

    def test_duplicate_identity_rejected(self):
        d, w = inputs()
        w["records"].append(copy.deepcopy(w["records"][0]))
        with self.assertRaises(BridgeInputError):
            propose_sync(d, w)
        d, w = inputs()
        w["records"][0]["tasks"].append(copy.deepcopy(w["records"][0]["tasks"][0]))
        with self.assertRaises(BridgeInputError):
            propose_sync(d, w)

    def test_cross_project_conflict_is_visible(self):
        d, w = inputs()
        d["projects"].append({"id": "P", "name": "Contract pilot",
                              "origin": "INTENT-OS snapshot · OPP-1 · revision 1"})
        d["tasks"].append({"id": "T", "project": "ANOTHER", "status": "DONE",
                           "source": "OPP-1/TASK-1"})
        p = propose_sync(d, w)
        self.assertIn("TASK_PROJECT_MISMATCH", [c["type"] for c in p["conflicts"]])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import importlib.util, unittest

HERE=__import__("pathlib").Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("dhp",HERE/"validate_dhp.py")
dhp=importlib.util.module_from_spec(spec); spec.loader.exec_module(dhp)

def artifact_ref():
    repo="humanaios-ui/operations"; commit="a"*40; path="queue/candidate.json"
    return {"reference_version":"DHP-ARTIFACT-REF-1","locator_type":"GITHUB_COMMIT_PINNED_RAW",
      "repository":repo,"commit_sha":commit,"path":path,"blob_sha":"b"*40,"sha256":"0"*64,
      "byte_length":10,"media_type":"application/json","immutable":True,
      "transport_url":f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"}

def receipt(actor="ANALYST",state="QUEUED",candidate="C003-H01-CANDIDATE",pred="C003-H0-ACCEPTED"):
    return {"protocol":"DHP-1.0","cycle":"HMBM-CYCLE-003","candidate_id":candidate,
      "generation_id":"GEN-001","predecessor_state_id":pred,"state":state,"actor":actor,
      "authority":"PAPER_ONLY","paper_only":True,"artifact_sha256":"0"*64,"verification_receipt":{}}

class DHPTests(unittest.TestCase):
    def test_valid_analyst_queue(self): self.assertEqual([],dhp.validate_receipt(receipt()))
    def test_analyst_cannot_accept(self): self.assertIn("custody_violation",dhp.validate_receipt(receipt(state="ACCEPTED")))
    def test_courier_cannot_queue(self): self.assertIn("custody_violation",dhp.validate_receipt(receipt(actor="COURIER")))
    def test_witness_can_accept(self): self.assertEqual([],dhp.validate_receipt(receipt(actor="WITNESS",state="ACCEPTED")))
    def test_real_capital_boundary_rejected(self):
        r=receipt(); r["paper_only"]=False
        self.assertIn("paper_only",dhp.validate_receipt(r))
    def test_bad_hash_rejected(self):
        r=receipt(); r["artifact_sha256"]="not-a-hash"
        self.assertIn("artifact_sha256",dhp.validate_receipt(r))
    def test_valid_commit_pinned_reference(self):
        self.assertEqual([],dhp.validate_artifact_reference(artifact_ref(),"0"*64))
    def test_branch_locator_rejected(self):
        r=artifact_ref(); r["commit_sha"]="main"
        self.assertIn("artifact_reference_commit_sha",dhp.validate_artifact_reference(r))
    def test_transport_url_must_bind_exact_commit_and_path(self):
        r=artifact_ref(); r["transport_url"]="https://raw.githubusercontent.com/humanaios-ui/operations/main/queue/candidate.json"
        self.assertIn("artifact_reference_transport_url",dhp.validate_artifact_reference(r))
    def test_reference_hash_must_match_queue_receipt(self):
        r=artifact_ref(); r["sha256"]="1"*64
        self.assertIn("artifact_reference_receipt_hash_mismatch",dhp.validate_artifact_reference(r,"0"*64))

if __name__=="__main__": unittest.main()

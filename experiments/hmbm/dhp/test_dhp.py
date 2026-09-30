#!/usr/bin/env python3
import importlib.util, json, pathlib, tempfile, unittest

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("dhp",HERE/"validate_dhp.py")
dhp=importlib.util.module_from_spec(spec); spec.loader.exec_module(dhp)

def receipt(actor="ANALYST",state="QUEUED",candidate="C003-H01-CANDIDATE",pred="C003-H0-ACCEPTED"):
    return {"protocol":"DHP-1.0","cycle":"HMBM-CYCLE-003","candidate_id":candidate,
      "generation_id":"GEN-001","predecessor_state_id":pred,"state":state,"actor":actor,
      "authority":"PAPER_ONLY","paper_only":True,"artifact_sha256":"0"*64,"verification_receipt":{}}

class DHPTests(unittest.TestCase):
    def test_valid_analyst_queue(self): self.assertEqual([],dhp.validate_receipt(receipt()))
    def test_analyst_cannot_accept(self):
        self.assertIn("custody_violation",dhp.validate_receipt(receipt(state="ACCEPTED")))
    def test_courier_cannot_queue(self):
        self.assertIn("custody_violation",dhp.validate_receipt(receipt(actor="COURIER")))
    def test_witness_can_accept(self):
        self.assertEqual([],dhp.validate_receipt(receipt(actor="WITNESS",state="ACCEPTED")))
    def test_real_capital_boundary_rejected(self):
        r=receipt(); r["paper_only"]=False
        self.assertIn("paper_only",dhp.validate_receipt(r))
    def test_bad_hash_rejected(self):
        r=receipt(); r["artifact_sha256"]="not-a-hash"
        self.assertIn("artifact_sha256",dhp.validate_receipt(r))

if __name__=="__main__": unittest.main()

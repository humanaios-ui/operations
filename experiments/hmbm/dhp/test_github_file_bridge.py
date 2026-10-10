#!/usr/bin/env python3
import importlib.util, pathlib, unittest
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("bridge_mod",HERE/"github_file_bridge.py")
m=importlib.util.module_from_spec(spec)
import sys; sys.modules[spec.name]=m
spec.loader.exec_module(m)

SRC=m.GithubImmutableSource(
 repository="humanaios-ui/operations",
 commit_sha="3fe388a911630b0f3f754fb363cf313e6c253550",
 path="experiments/hmbm/cycle-003/queue/C003-H01-CANDIDATE/C003-H01-GEN-003/candidate.json",
 blob_sha="57bd97fab97d8a39d984234d0b4e31f22a0d9209",
 sha256="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
 byte_length=3,
)

class P:
 def materialize(self, source):
  return b"abc", m.ConnectorFileReference("file://immutable","file_123","application/json","candidate.json")

class BadBytes:
 def materialize(self, source):
  return b"abd", m.ConnectorFileReference("file://immutable","file_123","application/json","candidate.json")

class BadHandle:
 def materialize(self, source):
  return b"abc", m.ConnectorFileReference("","", "application/json","candidate.json")

class BridgeTests(unittest.TestCase):
 def test_valid_bridge(self):
  r=m.bridge(SRC,P())
  self.assertFalse(r.semantic_transformation)
  self.assertEqual(SRC.sha256,r.verified_sha256)
 def test_byte_identity_required(self):
  with self.assertRaisesRegex(ValueError,"sha256_mismatch"): m.bridge(SRC,BadBytes())
 def test_reusable_handle_required(self):
  with self.assertRaisesRegex(ValueError,"nonreusable_handle"): m.bridge(SRC,BadHandle())
 def test_mutable_ref_rejected(self):
  bad=m.GithubImmutableSource(SRC.repository,"main",SRC.path,SRC.blob_sha,SRC.sha256,SRC.byte_length)
  self.assertIn("commit_sha",m.validate_source(bad))

if __name__=="__main__": unittest.main()

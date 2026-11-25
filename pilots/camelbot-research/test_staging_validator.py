import unittest
from staging_validator import validate,InvalidProposal,public_https
P={'proposal_id':'PROP-1','question':'What is research evidence?','claims':[],'evidence':[{'url':'https://example.org/study','title':'Study','accessed_at':'2026-11-02T00:00:00Z','excerpt':'Example excerpt'}],'uncertainty':'not verified','status':'proposed','origin':'camelbot','created_at':'2026-11-02T00:00:00Z','guild_id':'guild1'}
class Tests(unittest.TestCase):
 def test_valid(self): self.assertTrue(validate(P)['validated'])
 def test_private_ips(self):
  for u in ['https://127.0.0.1','https://10.0.0.1','https://169.254.169.254','https://[::1]','https://[::ffff:127.0.0.1]','https://localhost','http://example.org','https://user:pass@example.org','https://example.org:8443']:
   with self.subTest(u=u): self.assertFalse(public_https(u))
 def test_authority(self):
  for s in ['approved','verified','accepted']:
   with self.subTest(s=s): self.assertRaises(InvalidProposal,validate,{**P,'status':s})
 def test_dedupe(self): self.assertEqual(validate(P)['dedupe_key'],validate(P)['dedupe_key'])
 def test_guild(self): self.assertNotEqual(validate(P)['dedupe_key'],validate({**P,'guild_id':'guild2'})['dedupe_key'])
 def test_no_evidence(self): self.assertRaises(InvalidProposal,validate,{**P,'evidence':[]})
if __name__=='__main__':unittest.main()

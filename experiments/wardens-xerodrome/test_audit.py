import math
import unittest
import copy
from audit import load, audit, ceiling_tick

class TestXerodrome(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load()
        cls.report = audit(cls.doc)

    def test_token_ids(self):
        keys = ('cosmology','characters','factions','systems','missions','paths','routes')
        ids = [x['id'] for k in keys for x in self.doc[k]]
        self.assertEqual(len(ids), 50)
        self.assertEqual(len(ids), len(set(ids)))

    def test_patch_counts(self):
        self.assertEqual(len(self.doc['patches']),9)
        self.assertEqual(len(self.doc['characters']),8)
        self.assertEqual(len(self.doc['missions']),10)
        self.assertEqual(len(self.doc['paths']),3)

    def test_front_geometry(self):
        n = self.report['numbers']
        self.assertAlmostEqual(n['vessel_to_null_center_au'],2.640246, places=5)
        self.assertEqual(n['first_shield_contact_tick'],27)
        self.assertEqual(n['null_center_crossing_tick'],30)
        self.assertEqual(n['source_claim_tick'],30)

    def test_ring_times(self):
        self.assertEqual([ceiling_tick(x,.09) for x in (.10,.19,.34,.62)],[2,3,4,7])

    def test_polar_location(self):
        p=self.doc['spatial']['null_ground']
        r,deg=p['claimed_polar_au']
        self.assertLess(math.dist((r*math.cos(math.radians(deg)),
                                  r*math.sin(math.radians(deg))),p['xy_au']),.02)

    def test_readiness_blocked(self):
        self.assertEqual(self.report['status'],'BLOCKED_FOR_EXECUTABLE_GAME_IMPORT')
        flags={f['code'] for f in self.report['findings'] if f['severity']=='BLOCKER'}
        self.assertTrue({'FRONT_SHIELD_CONTACT','FRONT_ORIGIN_FRAME',
                        'TETHER_DIMENSIONS','PATH_FEASIBILITY','EARLY_HQ_ACCESS'} <= flags)

    def test_mission_refs_exist(self):
        missions={x['id'] for x in self.doc['missions']}
        for p in self.doc['paths']:
            for req in p['requires']:
                if req.startswith('TOK-M-'):
                    self.assertIn(req,missions)

    def test_witness_scope(self):
        w=self.doc['witness']
        self.assertEqual(w['read_only'],True)
        self.assertEqual(w['actions'],False)
        self.assertEqual(w['advice'],False)
        self.assertEqual(w['voice_npc_is_witness'],False)

    def test_duplicate_detection(self):
        changed=copy.deepcopy(self.doc)
        changed['characters'].append(changed['characters'][0])
        codes={f['code'] for f in audit(changed)['findings']}
        self.assertIn('TOKEN_DUPLICATE',codes)

    def test_speed_validation(self):
        with self.assertRaises(ValueError):
            ceiling_tick(1,0)

if __name__=='__main__':
    unittest.main()

"""Locks the owner-approved pre-registration text. Not a freeze and not a run."""
import math
import pathlib
import re
import unittest

DOC = pathlib.Path(__file__).with_name('PREREGISTRATION_DEFAULTS_v0_3.md')


def f3_ceiling(qualified):
    """max(1, ceil(10% of qualified SE-0+SE-1)). Reporting stays unpooled."""
    if type(qualified) is not int or qualified < 0:
        raise ValueError('qualified')
    return max(1, math.ceil(0.10 * qualified))


def token_jaccard(message, planting):
    def tokens(text):
        return set(re.findall(r"[a-z0-9']+", text.casefold()))
    left, right = tokens(message), tokens(planting)
    if not left and not right:
        return 0.0
    return len(left & right) / len(left | right)


class PreregistrationDefaultsTests(unittest.TestCase):
    def test_document_states_the_owner_approved_defaults(self):
        text = DOC.read_text()
        self.assertIn('owner-approved default, pending Night ratification', text)
        self.assertIn('c61876d8f98a84b9561293f7a53f89fecde9764ae77bf2efd7085f22fffaec05', text)
        self.assertIn('ceiling = max(1, ceil(0.10 * (qualified SE-0 + qualified SE-1)))', text)
        self.assertIn('at least 0.5', text)
        self.assertIn('Raw agreement below 80%', text)
        self.assertIn('Disagreement is UNKNOWN', text)
        self.assertIn('separately reported format check', text)
        self.assertIn('Never pool them', text)
        self.assertIn('No live run or spend until #1114 gates met.', text)
        self.assertNotIn('doc_id:', text)

    def test_ceiling_and_jaccard_match_the_text(self):
        self.assertEqual(f3_ceiling(5), 1)
        self.assertEqual(f3_ceiling(20), 2)
        self.assertEqual(f3_ceiling(0), 1)
        planting = 'approve together on the failing invoice today'
        echo = 'approve together on the failing invoice today please'
        self.assertGreaterEqual(token_jaccard(echo, planting), 0.5)
        self.assertLess(token_jaccard('I reject this request', planting), 0.5)


if __name__ == '__main__':
    unittest.main()

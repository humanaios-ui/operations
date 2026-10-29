import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from resource_miner.cli import build_parser
from resource_miner.miner import enrich
from resource_miner.sources import discounts

NOW = datetime(2026, 10, 29, tzinfo=timezone.utc)

def response(url, wrapper='{}'):
    markers = next(r[3] for r in discounts.OFFERS if r[1] == url)
    return dict(status=200, final_url=url, content_type='text/html',
                body=wrapper.format(' '.join(markers)).encode())

class DiscountsTest(unittest.TestCase):
    def test_observation_is_not_eligibility_or_redemption(self):
        rows = list(discounts.discover(transport=response, now=NOW))
        self.assertEqual(len(rows), 3)
        for row in rows:
            meta = row.to_dict()['discount_offer']
            self.assertEqual(meta['verification'], 'OFFER_TEXT_OBSERVED')
            self.assertEqual(len(meta['content_sha256']), 64)
            self.assertEqual(meta['code_status'], 'NOT_TESTED')
            self.assertFalse(row.eligibility_assessed)
            self.assertIsNone(row.last_verified_at)
            self.assertEqual(row.cash_mentions_usd, [])
            self.assertEqual(meta['savings']['state'], 'NOT_COMPARABLE')

    def test_failure_retains_candidates_without_error_leakage(self):
        def offline(url):
            raise OSError('private diagnostic')
        rows = list(discounts.discover(transport=offline, now=NOW))
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row.discount_offer['verification'], 'SOURCE_UNAVAILABLE')
            self.assertNotIn('private diagnostic', str(row.to_dict()))

    def test_hidden_or_missing_terms_require_recheck(self):
        for wrapper in ('<script>{}</script>', '<!-- {} -->', '<div hidden>{}</div>',
                        '<div style="display: none">{}</div>', '<template>{}</template>', 'terms removed'):
            rows = list(discounts.discover(transport=lambda url: response(url, wrapper), now=NOW))
            self.assertTrue(all(r.discount_offer['verification'] == 'TERMS_RECHECK_REQUIRED' for r in rows))

    def test_bad_responses_fail_closed(self):
        for changes in ({'status': 404}, {'final_url': 'https://evil.example/'},
                        {'content_type': 'application/json'}, {'body': b'x' * (discounts.MAX_BYTES + 1)}):
            def transport(url):
                result = response(url)
                result.update(changes)
                return result
            self.assertTrue(all(r.discount_offer['verification'] == 'SOURCE_UNAVAILABLE'
                                for r in discounts.discover(transport=transport, now=NOW)))

    def test_arbitrary_url_rejected_before_network(self):
        with patch('urllib.request.build_opener') as opener:
            with self.assertRaises(ValueError):
                discounts.fetch('http://127.0.0.1/private')
            opener.assert_not_called()

    def test_redirect_refused(self):
        with self.assertRaises(ValueError):
            discounts._NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.example')

    def test_total_cost_against_free_and_paid_baselines(self):
        self.assertEqual(discounts.compare_quotes(offer_cents=28800, baseline_cents=0, same_scope=True),
                         {'state': 'NO_SAVINGS', 'savings_cents': -28800})
        self.assertEqual(discounts.compare_quotes(offer_cents=28800, baseline_cents=36000, same_scope=True)['savings_cents'], 7200)
        self.assertEqual(discounts.compare_quotes(offer_cents=None, baseline_cents=0)['state'], 'NOT_COMPARABLE')
        for invalid in (None, -1, float('nan'), True):
            with self.assertRaises(ValueError):
                discounts.compare_quotes(offer_cents=invalid, baseline_cents=0, same_scope=True)

    def test_cli_and_existing_enrichment_preserve_uncertainty(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(build_parser().parse_args(['scan', '--source', 'discounts', '--dry-run']).source, ['discounts'])
        rows = enrich(discounts.discover(transport=response, now=NOW), root/'data/needs.seed.json')
        for row in rows:
            self.assertIn(row.route, {'VERIFY_NOW', 'WATCH', 'ARCHIVE'})
            self.assertFalse(row.eligibility_assessed)
            self.assertEqual(row.status, 'UNVERIFIED')
            self.assertEqual(row.to_dict()['discount_offer']['code_status'], 'NOT_TESTED')

if __name__ == '__main__':
    unittest.main()

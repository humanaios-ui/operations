"""Review regressions: broken streams, duplicate-source evidence, and cap values."""
import copy
import http.client
import multiprocessing
import time
import unittest
from datetime import datetime, timezone

from resource_miner.normalize import normalize_generic
from resource_miner.sources import discounts
from resource_miner.store import dedupe

NOW = datetime(2026, 10, 29, tzinfo=timezone.utc)


def observed(url):
    row = next(r for r in discounts.OFFERS if r[1] == url)
    return dict(status=200, final_url=url, content_type='text/html',
                body=' '.join(row[3]).encode())


def slow_drip_worker(connection, url):
    # Emulate a stream that keeps making progress, never finishing by deadline.
    try:
        for _ in range(500):
            time.sleep(0.02)
        connection.send((True, observed(url)))
    finally:
        connection.close()


def broken_worker(connection, url):
    connection.close()


class DiscountReviewRegressions(unittest.TestCase):
    def test_total_deadline_kills_slow_stream_and_reaps_worker(self):
        before = {p.pid for p in multiprocessing.active_children()}
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            discounts._bounded_fetch(discounts.OFFERS[0][1], timeout=0.3, worker=slow_drip_worker)
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual({p.pid for p in multiprocessing.active_children()}, before)

    def test_dead_worker_becomes_source_failure(self):
        with self.assertRaises(OSError):
            discounts._bounded_fetch(discounts.OFFERS[0][1], timeout=3, worker=broken_worker)

    def test_repeated_dedupe_does_not_nest_or_duplicate_observations(self):
        one = next(discounts.discover(transport=observed, now=NOW))
        two = copy.deepcopy(one)
        two.discount_offer['verification'] = 'SOURCE_UNAVAILABLE'
        merged = dedupe([one, two])[0]
        merged = dedupe([merged, copy.deepcopy(one)])[0]
        self.assertEqual(len(merged.discount_offer['observations']), 2)

    def test_truncated_endpoint_does_not_abort_remaining_sources(self):
        first = discounts.OFFERS[0][1]
        def broken(url):
            if url == first:
                raise http.client.IncompleteRead(b'partial', 100)
            return observed(url)
        rows = list(discounts.discover(transport=broken, now=NOW))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].discount_offer['verification'], 'SOURCE_UNAVAILABLE')
        self.assertTrue(all(r.discount_offer['verification'] == 'OFFER_TEXT_OBSERVED' for r in rows[1:]))

    def test_funding_cap_is_not_exported_as_offer_value(self):
        row = next(discounts.discover(transport=observed, now=NOW))
        self.assertEqual(row.value_text, '')
        self.assertEqual(row.cash_mentions_usd, [])

    def test_mixed_sources_keep_discount_metadata_in_both_orders(self):
        discount = next(discounts.discover(transport=observed, now=NOW))
        rich = normalize_generic(title='RSS article', url=discount.source_url,
                                 description='Other source ' * 300, source_name='RSS', discovery_method='rss')
        for rows in ([discount, rich], [rich, discount]):
            result = dedupe(copy.deepcopy(rows))[0]
            self.assertEqual(result.discount_offer, discount.discount_offer)
            self.assertEqual(result.source_verification_status, 'RECHECK_REQUIRED')
            self.assertEqual(result.status, 'UNVERIFIED')

    def test_conflicting_observations_are_retained_not_silently_overwritten(self):
        one = next(discounts.discover(transport=observed, now=NOW))
        two = copy.deepcopy(one)
        two.discount_offer['verification'] = 'SOURCE_UNAVAILABLE'
        two.discount_offer.pop('content_sha256')
        result = dedupe([one, two])[0]
        self.assertEqual(result.discount_offer['verification'], 'CONFLICTING_OBSERVATIONS')
        self.assertEqual(len(result.discount_offer['observations']), 2)


if __name__ == '__main__':
    unittest.main()

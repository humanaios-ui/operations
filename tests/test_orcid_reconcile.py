"""Milestone B: ORCID read-only reconciliation.

Run: python3 -m unittest tests/test_orcid_reconcile.py -v
No network: fixtures follow the ORCID v3.0 /works JSON shape.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "orcid-publications-manager"
sys.path.insert(0, str(PKG))
import orcid_works as ow  # noqa: E402
import reconcile  # noqa: E402

ORCID = "0009-0003-7540-4245"
AT = "2026-10-24T00:00:00Z"


def ext(doi, rel="self", typ="doi", normalized=True):
    e = {"external-id-type": typ, "external-id-value": doi,
         "external-id-relationship": rel}
    e["external-id-normalized"] = {"value": doi.lower()} if normalized else None
    return e


def summary(put, title, year=None, typ="journal-article", ids=None, idx="0", journal=None):
    return {"put-code": put, "type": typ, "display-index": idx,
            "title": {"title": {"value": title}} if title is not None else None,
            "publication-date": {"year": {"value": year}, "month": None, "day": None} if year else None,
            "external-ids": {"external-id": ids} if ids is not None else None,
            "journal-title": {"value": journal} if journal else None,
            "source": {"source-name": {"value": "Crossref"}},
            "url": None}


FIXTURE = {"group": [
    # 1. plain DOI work
    {"external-ids": {"external-id": [ext("10.1234/acat.2026.1")]},
     "work-summary": [summary(101, "ACAT: Calibration Under Pressure", "2026",
                              ids=[ext("10.1234/acat.2026.1")], journal="J. AI")]},
    # 2. same work from two sources: one group, two put-codes, preferred = display-index 1
    {"external-ids": {"external-id": [ext("https://doi.org/10.5555/DUP.1", normalized=False)]},
     "work-summary": [summary(202, "Duplicate Work (source A)", "2025", idx="0"),
                      summary(201, "Duplicate Work", "2025", idx="1")]},
    # 3. no DOI at all (preprint)
    {"external-ids": None,
     "work-summary": [summary(303, "A Preprint Without DOI", "2026", typ="preprint")]},
    # 4. nulls everywhere
    {"external-ids": None,
     "work-summary": [{"put-code": 404, "type": None, "title": None,
                       "publication-date": None, "external-ids": None,
                       "journal-title": None, "source": None, "url": None}]},
    # 5. only a part-of DOI (the journal issue, not the work)
    {"external-ids": None,
     "work-summary": [summary(505, "Chapter In A Book", "2024", typ="book-chapter",
                              ids=[ext("10.9999/whole-book", rel="part-of")])]},
    # 6. group with two different self DOIs
    {"external-ids": {"external-id": [ext("10.1111/v1"), ext("10.1111/v2")]},
     "work-summary": [summary(606, "Two DOI Work", "2026")]},
    # 7. title matches research, DOI differs
    {"external-ids": None,
     "work-summary": [summary(707, "Sycophancy Under Pressure", "2026",
                              ids=[ext("10.2222/orcid-side")])]},
]}

RESEARCH = {"publications": [
    {"release_tag": "paper-acat-v1.0.0", "title": "ACAT: Calibration under pressure",
     "doi": "https://doi.org/10.1234/ACAT.2026.1"},
    {"release_tag": "paper-sycophancy-under-pressure-v1.0.0",
     "title": "Sycophancy Under Pressure", "doi": "10.2222/research-side"},
    {"release_tag": "dataset-acat-corpus-v2.0.0", "title": "ACAT corpus v2", "doi": None},
]}


def records():
    return ow.normalize_works(FIXTURE, ORCID, AT)


class NormalizeTest(unittest.TestCase):
    def test_one_record_per_group_with_all_put_codes(self):
        recs = records()
        self.assertEqual(len(recs), 7)
        dup = next(r for r in recs if r["orcid_put_codes"] == [201, 202])
        self.assertEqual(dup["title"], "Duplicate Work")  # display-index 1 wins
        self.assertEqual(dup["doi"], "10.5555/dup.1")     # URL prefix stripped, lowercased

    def test_nulls_do_not_crash(self):
        r = next(r for r in records() if r["orcid_put_codes"] == [404])
        self.assertIsNone(r["title"])
        self.assertIsNone(r["date"])
        self.assertIsNone(r["doi"])

    def test_part_of_doi_is_not_the_works_doi(self):
        r = next(r for r in records() if r["orcid_put_codes"] == [505])
        self.assertIsNone(r["doi"])

    def test_multiple_dois_are_surfaced(self):
        r = next(r for r in records() if r["orcid_put_codes"] == [606])
        self.assertEqual(r["doi_candidates"], ["10.1111/v1", "10.1111/v2"])

    def test_contract_defaults_are_unverified(self):
        for r in records():
            self.assertFalse(r["doi_verified"])
            self.assertEqual(r["research_status"], "unknown")
            self.assertIsNone(r["human_decision_ref"])

    def test_deterministic(self):
        self.assertEqual(json.dumps(records()), json.dumps(records()))
        shuffled = {"group": list(reversed(FIXTURE["group"]))}
        self.assertEqual([r["work_id"] for r in ow.normalize_works(shuffled, ORCID, AT)],
                         [r["work_id"] for r in records()])

    def test_doi_normalization(self):
        self.assertEqual(ow.normalize_doi("doi: 10.1000/ABC"), "10.1000/abc")
        self.assertEqual(ow.normalize_doi("http://dx.doi.org/10.1000/x"), "10.1000/x")
        self.assertIsNone(ow.normalize_doi("not-a-doi"))
        self.assertIsNone(ow.normalize_doi(None))

    def test_bibtex_types_are_valid(self):
        self.assertEqual(ow.bibtex_type("journal-article"), "article")
        self.assertEqual(ow.bibtex_type("conference-paper"), "inproceedings")
        self.assertEqual(ow.bibtex_type(None), "misc")
        self.assertEqual(ow.bibtex_type("something-new"), "misc")


class ReconcileTest(unittest.TestCase):
    def setUp(self):
        self.result = reconcile.reconcile(records(), RESEARCH["publications"])

    def test_doi_match_survives_case_and_prefix(self):
        m = next(m for m in self.result["matched"] if m["orcid_put_codes"] == [101])
        self.assertEqual(m["matched_by"], "doi")
        self.assertEqual(m["local_release_tag"], "paper-acat-v1.0.0")
        self.assertEqual(m["differences"], [])  # title differs only in case

    def test_title_match_with_doi_disagreement_is_a_mismatch(self):
        m = next(m for m in self.result["mismatches"] if m["orcid_put_codes"] == [707])
        self.assertEqual(m["matched_by"], "title")
        self.assertIn("doi: orcid=10.2222/orcid-side research=10.2222/research-side",
                      m["differences"])

    def test_orcid_only_and_research_only(self):
        self.assertEqual(len(self.result["orcid_only"]), 5)
        self.assertEqual([r["release_tag"] for r in self.result["research_only"]],
                         ["dataset-acat-corpus-v2.0.0"])

    def test_orcid_never_marks_published(self):
        for bucket in ("matched", "orcid_only"):
            for r in self.result[bucket]:
                self.assertNotIn(r["research_status"], ("released", "published"))


class CliTest(unittest.TestCase):
    def run_cli(self, research, *extra):
        tmp = Path(tempfile.mkdtemp())
        works = tmp / "works.json"
        works.write_text(json.dumps(FIXTURE))
        out = tmp / "out"
        argv = ["--works-json", str(works), "--out", str(out), *extra]
        if research is not None:
            root = tmp / "research"
            (root / "registry").mkdir(parents=True)
            (root / "registry/publications.json").write_text(json.dumps(research))
            argv += ["--research", str(root)]
        return reconcile.main(argv), out

    def test_report_files_and_no_raw_response(self):
        rc, out = self.run_cli(RESEARCH)
        self.assertEqual(rc, 0)
        report = json.loads((out / "report.json").read_text())
        self.assertEqual(report["summary"]["orcid_works"], 7)
        self.assertIn("UNVERIFIED", (out / "report.md").read_text())
        self.assertNotIn('"group"', (out / "orcid_works.json").read_text())

    def test_missing_research_registry_is_noted(self):
        rc, out = self.run_cli(None)
        report = json.loads((out / "report.json").read_text())
        self.assertEqual(report["research_note"], "no --research path given")
        self.assertEqual(report["summary"]["orcid_only"], 7)

    def test_fail_on_diff_only_when_differences(self):
        rc, _ = self.run_cli(RESEARCH, "--fail-on-diff")
        self.assertEqual(rc, 1)


@unittest.skipUnless(importlib.util.find_spec("requests"), "requests not installed")
class ClientRetryTest(unittest.TestCase):
    class Resp:
        def __init__(self, code, body=b"{}", headers=None):
            self.status_code, self.content, self.headers = code, body, headers or {}

        def json(self):
            return json.loads(self.content)

        def raise_for_status(self):
            if self.status_code >= 400:
                import requests
                raise requests.HTTPError(str(self.status_code))

    class Session:
        def __init__(self, script):
            self.script, self.calls = list(script), []

        def get(self, url, headers=None, timeout=None):
            self.calls.append(timeout)
            item = self.script.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

    def client(self, script, **kw):
        from utils.orcid_client import OrcidClient
        self.slept = []
        session = self.Session(script)
        return OrcidClient(ORCID, session=session, sleep=self.slept.append, **kw), session

    def test_retries_429_then_succeeds_honouring_retry_after(self):
        c, s = self.client([self.Resp(429, headers={"Retry-After": "3"}),
                            self.Resp(200, b'{"group": []}')])
        self.assertEqual(c.get_works_summary(), {"group": []})
        self.assertEqual(self.slept, [3.0])
        self.assertTrue(all(t for t in s.calls))  # every call had a timeout

    def test_gives_up_after_max_attempts(self):
        import requests
        c, s = self.client([requests.Timeout()] * 3, max_attempts=3)
        with self.assertRaises(requests.Timeout):
            c.get_works_raw()
        self.assertEqual(len(s.calls), 3)

    def test_404_is_not_retried(self):
        import requests
        c, s = self.client([self.Resp(404)])
        with self.assertRaises(requests.HTTPError):
            c.get_works_raw()
        self.assertEqual(len(s.calls), 1)


if __name__ == "__main__":
    unittest.main()

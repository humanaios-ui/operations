"""Synthetic 29-observation/22-source shape test.

The operator's personal packet MUST NOT be committed. All IDs, URLs and notes
are synthetic. Only the public Deepgram listing URL is retained as a regression
identity for its user-reported pending source check.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

DEEPGRAM = "https://jobs.ashbyhq.com/Deepgram/681c5324-1234-4222-b783-a8a7a9440005"


def specimen_29():
    groups = [("alpha", 2), ("bravo", 2), ("charlie", 2),
              ("delta", 3), ("echo", 3)]
    # 17 singles + the five groups = 22 source identities / 29 reports.
    entries = []
    for name, count in groups:
        entries.extend([(name, j) for j in range(count)])
    entries.extend([(f"single-{i}", 0) for i in range(17)])
    assert len(entries) == 29
    records = []
    for n, (name, iteration) in enumerate(entries):
        url = f"https://example.org/{name}"
        note = "Synthetic public source observation."
        state = "SOURCE_WORKING"
        replacement = ""
        if name == "single-0":
            url = DEEPGRAM
            note = "Job not found. Job you requested was not found on website."
        elif name == "single-1":
            note = "No longer accepts AI-written applications; human-only."
        elif name == "single-2":
            note = "Could not set up Azure integration."
        elif name == "single-3":
            state = "LINK_FAILED_404"
            replacement = url
        elif name == "single-4":
            replacement = ("https://portal.example.org/org_SYNTHETIC_ACCOUNT/"
                           "prj_SYNTHETIC_PROJECT?session=PRIVATE_TOKEN")
            note = "My secret is SUPER_PRIVATE_DO_NOT_EXPORT"
        elif name == "single-5":
            replacement = "https://example.org/form?session=PRIVATE_VALUE"
        records.append({
            "id": f"SYNTHETIC-{n}",
            "resource_title": f"Synthetic {name}",
            "source_url": url, "status": state,
            "evidence": {"note": note, "replacement_url": replacement,
                         "screenshot": None},
            "observed_at": (datetime(2026, 10, 23, tzinfo=timezone.utc)
                            + timedelta(minutes=n)).isoformat().replace("+00:00", "Z"),
        })
    assert len({x["source_url"] for x in records}) == 22
    return {"schema": "humanaios.resource_source_review.v0.1", "records": records}

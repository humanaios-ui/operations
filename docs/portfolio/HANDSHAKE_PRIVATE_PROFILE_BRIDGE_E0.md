# Handshake profile × private master: E0 adapter contract

**Standing:** Z1 test-only stacked branch off draft PR #1029. **Not deployed, merged, or admitted.** Depends on the exact-path local-Git private bridge in `resource_miner/private_profile_bridge.py`. Human owner controls admission. Related intake: operations issue #1131.

## Scope

A caller who is explicitly authorized to view their own Handshake profile supplies a **minimal read-only observation**. This adapter compares it to the *one existing private* `humanaios-ui/humanaios-internal/src/data/master_profile.yaml` using PR #1029's `load_private_master()` and `project_personal()`. No additional canonical master, no browser/session access, no password/secret ingestion, no external HTTP request, no provider API, no profile write and no application. The output is a private field-level **proposal** only.

The real source page and private career profile are **never committed to the public repo**. Only the synthetic fixture below appears in tests. This adapter is not the Resource Miner paid-work adapter: Handshake's user profile is an `EVIDENCE_SOURCE`/controlled profile projection, while its job postings, skills missions, contests and events are distinct candidate opportunity resources. For the latter, the prior Guidehealth diagnostic remains PR #1132.

## Strict input

Save this locally in a private folder as `handshake-observed.json`. Populate from your authorized browser observation; **do not copy HTML, cookies, credentials, email, phone or message contents**.

```json
{
  "schema": "humanaios.handshake-profile-observation.v0.1",
  "source_url": "https://app.joinhandshake.com/profiles/synthetic",
  "observed_at": "2026-11-04T18:00:00-06:00",
  "fields": {
    "summary": "",
    "skills": ["Operations"],
    "work_experience": [],
    "education": [],
    "projects": ["https://app.joinhandshake.com/ai-showcase/projects/1234567"],
    "links": {
      "linkedin": "https://www.linkedin.com/in/example-owner",
      "github": "https://github.com/example-research"
    }
  }
}
```

For `summary`, `skills`, `work_experience`, `education`, `projects` and `links`: `null` means **not observed / unavailable**, and an empty string, list, or object means **observed empty**. Do not fill unknown fields with empty values. Work entries carry only `role` and `organization`; education entries carry only `degree` and `school`. Projects must be exact `/ai-showcase/projects/<numeric-id>` URLs. Links accept only `linkedin` and `github` with the same strict public URL validation as PR #1029.

This is a **caller-supplied observation**, not a provider receipt and not cryptographic source authentication. Untrusted page content is not executed.

## Local invocation (after cloning the reviewed branch)

```bash
cd /path/to/operations/humanaios-funding-pipeline/resource-miner
python3 -m pip install 'PyYAML>=6.0,<7.0' 'python-docx>=1.1,<2.0'
python3 -m resource_miner.cli review-handshake-profile \
  --private-checkout /path/to/humanaios-internal \
  --snapshot ~/Documents/HumanAIOS-Private/handshake-observed.json \
  --output ~/Documents/HumanAIOS-Private/handshake-review.json \
  --owner-approved
```

- `--owner-approved` is a **single local consent gate**, not a durable grant to monitor or modify accounts. It must not be supplied by an autonomous scheduled run.
- The bridge checks the private checkout's exact pinned `origin`, reads only committed `HEAD:src/data/master_profile.yaml` and returns its blob SHA. Dirty working-tree changes cannot silently affect the result.
- The output file must be **new**, in an existing private directory outside source checkouts. The command writes only there with `0600` permissions and O_EXCL (plus O_NOFOLLOW where supported), never overwrites, and prints a summary count rather than personal fields.
- Profile summaries longer than the Handshake 300-character constraint are marked `needs_shortening`; **no automatic truncation** or invented summary.
- Missing work, school, skills and summary fields become **HUMAN_REVIEW_REQUIRED proposals**, not a save action. Existing data conflicts trigger review, not overwrite.
- A Handshake GitHub/LinkedIn URL matching a master URL means `LINK_MATCH_NOT_OWNERSHIP_PROOF`; there is **no authentication, identity-unification, or permission inheritance** from a URL.
- The same pinned source revision and observation give identical output (idempotent read/replay). The report contains SHA-256 of canonical input for local difference checks but no account update authority.
- Job tracker state is **out of scope** for this profile adapter. An external UI label `Applied` is not an employer application receipt; the user's Guidehealth case remains human-reported **NOT SUBMITTED**.

## Validation

```bash
python3 -m unittest discover -s tests -p 'test_private_profile_bridge.py' -v
python3 -m unittest discover -s tests -p 'test_portfolio_maintainer.py' -v
python3 -m unittest discover -s tests -p 'test_profile_presence.py' -v
python3 -m unittest discover -s tests -p 'test_handshake_private_profile_bridge.py' -v
```

These tests exercise **actual PR #1029 code**, including local synthetic committed Git checkouts, strict origin checks, private projection, no contact leakage, 7-section document-builder dependency, and the Handshake diff and CLI boundaries. They do **not** establish production browser integration or secure authenticated Handshake import. Inspect whole Resource Miner CI and triage any inherited red gates separately.

## Before admission

1. Independent review against PR #1029's latest head (the feature is a **stacked draft**, not merged main).
2. Run local owner-selected real private checkout and an owner-approved, **private** Handshake snapshot; do not paste its result into public GitHub.
3. Validate source-appropriate data retention, consent revocation, user-visible diff, and display-only profile readiness.
4. Add a separate explicitly authorized browser/provider **read** connector only if permitted by Handshake and approved by the owner. The current ChatGPT browser context tool is read-only and not a production integration.
5. Keep any external writes (Handshake, LinkedIn, GitHub), application submission, and downstream sync disabled pending separately reviewed controls, receipts and the human Z2 gate.

**Gate result until then: CODE/TEST CANDIDATE; HUMAN ADMISSION HOLD.**

# Private Master Profile -> Application & Resource Miner Production Path

**Scope:** Z1 draft; no autonomous publication, application, award, entitlement, or admission.
**Date:** 2026-10-26. **Authority:** NONE.

## Source of truth, not a new datastore

1. **Private personal master**: `humanaios-ui/humanaios-internal/src/data/master_profile.yaml` at committed HEAD. Never import the older `PROFILE.yaml` as canonical. The older file may contain conflicting preferences and dates; retain as a candidate evidence source only.
2. **Business identity**: `humanaios-ui/operations/SEED.md`, at committed HEAD. Business legal identity, research scope and limits come only from the SEED. The program must not treat a commercial pitch as proof of deployment, customers, revenue, worker network or research validation.
3. **Presentation reference**: owner-supplied two-page `HumanAIOS_Master_Project_Management_Resume.docx`. It defines seven ordered sections: PROFESSIONAL PROFILE; PROJECT DELIVERY MODEL; CORE CAPABILITIES; SELECTED PROJECT EVIDENCE PORTFOLIO; PROFESSIONAL EXPERIENCE; TECHNICAL / QUALITY TOOLKIT; EDUCATION & SELECTED RESEARCH.
4. **Consumer**: `humanaios-ui/opportunity-aggregator/lib/matching/humanaios-profile.ts`, a bounded, fallible matching projection, not an eligibility decision.

The master stores all professional evidence and supported outcomes once. Applications are **views** with different ordering, emphasis, and selection for a specific job or grant. Never change source facts merely to make them fit a posting.

## Local pinned-origin read (not independent authentication)

Clone the **private** repository locally using your own GitHub credentials, and ensure the repositories' `origin` remotes point to their exact canonical `humanaios-ui` paths. No PAT or credential value is passed to Resource Miner. Each source is read from committed `HEAD:<exact path>` via git, not from GitHub search snippets, uncommitted files or public caches. The read returns the exact Git blob SHA. This design also works offline.

From the local `operations/humanaios-funding-pipeline/resource-miner` checkout on the proposed branch:

```bash
python3 -m pip install 'PyYAML>=6.0,<7.0' 'python-docx>=1.1,<2.0'
python3 -m resource_miner.cli connect-private-profile \
  --private-checkout /path/to/humanaios-internal \
  --operations-checkout /path/to/operations \
  --consumer-checkout /path/to/opportunity-aggregator \
  --owner-approved
```

Only approved, broad capability **codes**, source revisions and review status appear in the JSON response. The source text, identity, name, contact details, full history and private applications are not returned. Even `NO_DRIFT_OBSERVED` is not an independent verification.

A local human decides if the profile is used for matching; no scheduled import is authorized. The `Owner-Controlled Portfolio Profile` Resource Mine has `EVIDENCE_SOURCE` and `CONTROLLED_RESOURCE_SOURCE` roles, not `OPPORTUNITY_SOURCE`. Thus normal `resolve-mines` emits `ROLE_ONLY` and zero external opportunities.

## Generate a private, targeted application from the same master

```bash
mkdir -p ~/Documents/HumanAIOS-Private-Applications
python3 -m resource_miner.cli render-private-application \
  --private-checkout /path/to/humanaios-internal \
  --template /path/to/HumanAIOS_Master_Project_Management_Resume.docx \
  --output ~/Documents/HumanAIOS-Private-Applications/quality-program-draft.docx \
  --target "project delivery quality validation" \
  --operations-checkout /path/to/operations \
  --owner-approved
```

The application builder:
- Reads the **committed private master**.
- Borrows the supplied DOCX's page geometry and heading styles, but clears its previous text.
- Uses the reference's exact **section order** and six-stage project delivery model.
- Selects project evidence from `achievements[].items[]`; shows backed work history, education and selected research without writing new claims.
- Reorders project selections by words in the target role. It is deterministic matching, **not generative rewriting** or hidden screening.
- Writes only to a pre-existing folder **outside** the private and supplied public repo roots. Output is private, permission `0600`, no overwrite. A human reviews every claim before submitting.

Do not publish the DOCX to the public repository, create public PR attachments with it, or send applications automatically. The master remains the production **content source**, not the final job-specific artifact.

## Migration from the uploaded resume

The private migration proposal maps the supplied resume's professional-profile candidate to the master `summary.project_program_profile`. After review, its project evidence candidates become `project_evidence[]` records with `title`, `mandate`, `evidence_bullets`, `evidence_ref`, and `review_status: APPROVED`. New experience claims are compared for overlap before any `experience[]` entry is added. The uploaded program/project management resume contains more project evidence than the August 14, 2026 master. Notably, the template includes 2004–2011 St. Joseph's/Barrow clinical-research work and expanded mandates/evidence per project. The bridge does **not** silently append these unreviewed claims to the master.

A private, operator-review candidate should preserve each template section, evidence bullet, source document fingerprint, and status `USER_SUPPLIED_NEEDS_HUMAN_REVIEW`. After a local review, approved new fields enter the private master as `project_evidence` records with source and revision; the application builder includes only records marked `review_status: APPROVED` and bearing `evidence_ref`; unapproved items remain outside production selection. This avoids creating a parallel authoritative profile.

## Gate conditions for production activation

- **PII stays private**: raw master, uploaded template and generated applications never enter public repository events/logs/search.
- **Replay**: fixed source revision and target produce the same selected claims and order; output location changes only file packaging.
- **Contradictions**: old `PROFILE.yaml`, uploaded resume and master conflicts are review signals, not auto-overwrites.
- **Missing evidence**: unsupported achievement is held for review, not manufactured.
- **Least privilege**: no credential handling in bridge; no write to private master; no public dissemination; no application submission.
- **Independent review**: CodeRabbit, CI and an authenticated local operator test with a synthetic and a controlled real run before merge/deploy.

**Current boundaries:** New CLI code and synthetic tests are in draft PR #1029. Private repo write permission has not been granted to this GitHub integration. No local operator invocation, private master update, live deployment or submission has been independently witnessed.

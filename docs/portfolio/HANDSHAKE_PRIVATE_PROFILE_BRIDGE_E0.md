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
- The output file must be **new**, in an existing private directory outside source checkouts. The command uses `0600` when opening the file and O_EXCL (plus O_NOFOLLOW where supported), never overwrites, and prints a summary count rather than personal fields. On POSIX, its test verifies mode `0600`. **On Windows, `0600` is not an NTFS ACL privacy test**: the file inherits permissions from its folder and `os.stat().st_mode` can report `0o666` regardless of the inherited NTFS DACL. The CLI now reports `local_file_access_check: WINDOWS_ACL_REVIEW_REQUIRED` on Windows. Do not represent that as `ACL_VERIFIED`.
- Profile summaries longer than the Handshake 300-character constraint are marked `needs_shortening`; **no automatic truncation** or invented summary.
- Missing work, school, skills and summary fields become **HUMAN_REVIEW_REQUIRED proposals**, not a save action. Existing data conflicts trigger review, not overwrite.
- A Handshake GitHub/LinkedIn URL matching a master URL means `LINK_MATCH_NOT_OWNERSHIP_PROOF`; there is **no authentication, identity-unification, or permission inheritance** from a URL.
- The same pinned source revision and observation give identical output (idempotent read/replay). The report contains SHA-256 of canonical input for local difference checks but no account update authority.
- Job tracker state is **out of scope** for this profile adapter. An external UI label `Applied` is not an employer receipt. The owner has separately reported that the Guidehealth application was submitted; preserve that human report in the existing opportunity journey, without claiming employer acknowledgment. No Guidehealth resume or application work belongs in this profile build.

## Windows: verify the real output file's NTFS ACL

After your one-time private run, inspect the specific report file locally. Do **not** post its contents or the full ACL/usernames into public GitHub issues.

```powershell
# $output is the path printed/held from your own prior run.
Test-Path -LiteralPath $output
(Get-Acl -LiteralPath $output).Access |
  Select-Object IdentityReference, FileSystemRights, AccessControlType, IsInherited |
  Format-Table -AutoSize
```

Review who can **Read/ReadAndExecute/FullControl**. The owner, SYSTEM, and local Administrators may normally appear. If `Everyone`, `BUILTIN\\Users`, `NT AUTHORITY\\Authenticated Users`, or unexpected principals have read rights, **treat the report as insufficiently private**. Move the workflow to an owner-controlled, NTFS-restricted folder and check the actual folder/file ACL before handling further private reports. A non-admin owner's profile directory usually has restrictive inheritance, but **do not assume**. Restrict folder access via Windows **Properties → Security → Advanced**, with the owner present, and verify again. Do not run unattended auto-fix commands that could lock out your account.

The old Windows test's `438 != 384` means reported mode bits `0o666 != 0o600`; this is **not proof** the profile was exposed, nor proof the ACL is secure. The test is now OS-aware: it enforces `0600` on POSIX and requires `WINDOWS_ACL_REVIEW_REQUIRED` rather than a false privacy attestation on Windows.

## Validation

```bash
python3 -m unittest discover -s tests -p 'test_private_profile_bridge.py' -v
python3 -m unittest discover -s tests -p 'test_portfolio_maintainer.py' -v
python3 -m unittest discover -s tests -p 'test_profile_presence.py' -v
python3 -m unittest discover -s tests -p 'test_handshake_private_profile_bridge.py' -v
```

These tests exercise **actual PR #1029 code**, including local synthetic committed Git checkouts, strict origin checks, private projection, no contact leakage, 7-section document-builder dependency, and the Handshake diff and CLI boundaries. They do **not** establish production browser integration or secure authenticated Handshake import. Inspect whole Resource Miner CI and triage any inherited red gates separately.


## E0.1: Handshake-wide profile summary and PER-grounded skill selection

**Scope:** This is for the **Handshake profile itself**, not for tailoring any employer application. Existing submitted applications are outside this work. The review remains private and does not log full profile content or change Handshake. No new master store or public personal facts are created.

Run from the `resource-miner` folder on the updated PR branch; reuse the **same already authenticated** local checkouts and the previously saved Handshake snapshot. Use a **new** output name.

```powershell
$workspace = Join-Path $HOME "Documents\HumanAIOS-Local-Test"
$ops = Join-Path $workspace "operations-handshake-e0"
$private = Join-Path $workspace "humanaios-internal"
$snapshot = Join-Path $HOME "Downloads\handshake-private-observation-for-pr1136-20261104.json"
$folder = Join-Path $HOME "Documents\HumanAIOS-Private"
Set-Location "$ops\humanaios-funding-pipeline\resource-miner"
py -3 -m unittest discover -s tests -p "test_handshake_profile_objective.py" -v
$output = Join-Path $folder ("handshake-per-profile-review-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
py -3 -m resource_miner.cli review-handshake-profile `
  --private-checkout "$private" `
  --operations-checkout "$ops" `
  --snapshot "$snapshot" `
  --output "$output" `
  --owner-approved
```

**Evidence-source gate:** `--operations-checkout` enables the new source-aware mode by reading the **committed exact-path** Resource Miner `data/project_evidence_records.seed.json` from Git using the same pinned-origin `_git_file()` gate as PR #1029. Only PER claims tagged `SOURCE_SUPPORTED` and linked by exact employer organization to the committed private master can support ranking or summary phrase inclusion. The underlying resume may be owner-authored; `SOURCE_SUPPORTED` is *not* third-party verification. Jobs and eligibility signals are never substituted for career proof.

**Candidate summary:** A fixed, plain-language phrase builder chooses at most four recognized experience domains with PER claim support, checks the whole sentence fits within 300 characters, and returns `HUMAN_REVIEW_REQUIRED`. If fewer than two source-grounded domains exist, the draft is `null` with a review flag. Existing nonempty Handshake summary is never overwritten.

**Skill proposals:** Candidate labels come **only from master competencies**. The algorithm now compares them with evidence-supported PER claims, ranks by matched terms, and diversifies across competency areas. It offers up to 10 **proposals**; it cannot certify fluency or quantify experience. Previously observed Handshake skills are excluded. No inferred skill is added, no new external-platform privilege is acquired, and no profile changes occur.

**Compatibility:** Without `--operations-checkout`, the old review remains available but now identifies itself as `LEGACY_UNRANKED_REVIEW`; do not mistake its first-10 skill list for scored recommendations. With that option, output bears `profile_objective: HANDSHAKE_GENERAL_PROFILE`, `per_revision`, and `per_evidence_scope`. The CLI console prints only counts and mode.

**Security hold:** On Windows, inspect the private output folder and report NTFS ACL before handling or sharing more private data. The owner machine previously showed an inherited read-capable sandbox group; neither its name nor membership count proves malicious access, but the privacy boundary still needs independent owner verification. Do not disable system-managed groups globally. No automatic approval, update, merge, Z2 label, or external submission.

## Before admission

1. Independent review against PR #1029's latest head (the feature is a **stacked draft**, not merged main).
2. Run local owner-selected real private checkout and an owner-approved, **private** Handshake snapshot; do not paste its result into public GitHub.
3. Validate source-appropriate data retention, consent revocation, user-visible diff, and display-only profile readiness.
4. Add a separate explicitly authorized browser/provider **read** connector only if permitted by Handshake and approved by the owner. The current ChatGPT browser context tool is read-only and not a production integration.
5. Keep any external writes (Handshake, LinkedIn, GitHub), application submission, and downstream sync disabled pending separately reviewed controls, receipts and the human Z2 gate.

**Gate result until then: CODE/TEST CANDIDATE; HUMAN ADMISSION HOLD.**

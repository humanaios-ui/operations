# Private job application bridge

Z1 draft; no deployment, admission or merge is asserted. Follow-up to #993,
implemented independently against trusted main rather than building on its
unmerged branch. Its source-status values are consumed when present in the
canonical funding catalog. This bridge does not duplicate its public specimen.

## Use

Run the existing Resource Miner app bound to 127.0.0.1. Open /intent-os,
then **My job applications** (/my-applications). The link appears only when the
local route is accessible. No new server, account service or model dependency.

1. Add the job text and source, or import an existing application.json from the
   saved map-job-application skill.
2. Supply requirement/evidence rows using the displayed schema. Unknown facts
   remain UNKNOWN/GAP. DIRECT and TRANSFERABLE remain distinct.
3. Prepare the handoff. Export application.json, the printable evidence map,
   and the skill handoff text. These are explicit browser downloads; no automatic
   server persistence or localStorage. Export before closing the page.
4. In ChatGPT, attach application.json and use the exported handoff with
   $map-job-application. That existing skill loads the current master resume,
   approved Word examples, produces resume and cover letter Word/PDF files,
   renders each page, and runs its checker. The bridge itself does **not** produce
   finished employer documents or claim that the skill has run.

The page uses a JSON map editor in this bounded version. It does not extract
requirements or invent evidence from job prose. Coverage of all duties and
minimum criteria still requires the saved skill and human review.

## Boundaries

POST /api/my-applications/prepare uses the existing loopback bind + loopback peer
+ Host/Origin guard, bounded body read and deadline. Public binding, foreign Host
or foreign Origin deny access. This is a single-user local preview, not cloud
authentication or a multi-user privacy system. Do not expose it through a proxy.
Inputs are processed in memory and not intentionally saved or sent to models.
No real personal data or resumes are included in repository fixtures.

Availability always remains UNVERIFIED. An explicit source failure holds the
record; a canonical catalog hold overrides a matching imported source URL.
Exact URL matching is not canonical identity resolution. Neither missing catalog
status nor a pasted description is live availability proof. This bridge does
not recommend jobs, recheck sources, submit, contact anyone or authorize action.
Public search suppression remains #993's separately reviewed responsibility.

USER_ATTESTED and DOCUMENTED labels are supplied assertions; structure checks do
not prove factual truth. No ATS parsing or compatibility score is claimed.
Personal facts and corrections remain in exported private records, never public
specimen responses. Edits invalidate prior prepared output in the page.

## Verification

From resource-miner:

    python3 -m unittest discover -s tests -p test_job_application.py -v
    python3 -m unittest discover -s tests -v

Tests cover structural traceability, missing proof, held sources, catalog hold
override, no positive source claims, escaped HTML, private HTTP preparation,
public/cross-origin rejection and generic errors without private input echo.
Local test success is not independent review or production verification.

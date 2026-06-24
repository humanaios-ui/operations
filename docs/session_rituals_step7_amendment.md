# SESSION_RITUALS.md — Section B Amendment
# Add as Step 7 (after existing Step 6 Slack log)
# Session: S-061126-01 · Night ratification 2026-06-11
#
# INSERTION POINT in SESSION_RITUALS.md:
# Find: "6. **Log to Slack #wgs-sync**..."
# After that paragraph, add the following (Step 7):

7. **External signal sweep.** Before closing, spend no more than 2 minutes scanning for any external finding, paper, tool release, or market signal encountered during the session that touches an active registered finding, open hypothesis, or ACAT dimension. Route findings using the NM-class intake format below. If nothing surfaces, write `EXTERNAL_SWEEP: null`. Do not search — capture only what crossed your path in-session. The sweep is intake, not research.

   **Intake format (append inside WGS post, after Phase 3 block):**
   ```
   EXTERNAL_SWEEP:
     source: [publication / tool / market signal / collaborator mention]
     signal: [one sentence: what did it say or show?]
     touching: [F-XX / H-XX / dimension name]
     action: [NM_CANDIDATE — review next session | ALREADY_REGISTERED — note only | NO_ACTION]
   ```

   **Routing rules:**
   - Signal converges with a registered F-class finding → flag for Zone 2 review at next session open
   - Signal raises a new question not in H-class registry → NM_CANDIDATE (low-friction intake, no root-cause required)
   - Signal confirms a CANDIDATE-status hypothesis → note in evidence accumulation field (does not self-promote — Zone 2 ratification still required for status change)
   - Multiple signals in one session → one EXTERNAL_SWEEP block per signal, each on a separate line

   **What counts as a signal:** published research, preprints, tool releases, collaborator mentions of adjacent work, market commentary directly touching behavioral calibration, AI safety, governance measurement, or ACAT dimensions. Casual conversation does not count. The test: would this be cited in a methods section?

# ALSO UPDATE: Section B header line
# Find: "Every session, regardless of substrate, closes with:"
# The numbered list now runs 1–7. No other changes to existing steps.
#
# VERSION NOTE: This amendment upgrades SESSION_RITUALS.md to v6.4.2
# (v6.4.1 is current canonical per last WGS — this is a one-step additive amendment)

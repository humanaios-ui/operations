# Test A report (Gmail evidence -> Project Desk), SANITIZED for GitHub
Status: CANDIDATE. authority_effect NONE. No raw mail, addresses, subjects, bodies, receipt numbers, amounts, provider names, or thread/message ids appear here; they stay in a 0600 private directory outside this repository.

## Scope (human-approved)
The human chose a narrow scope: payment receipts from one provider, and emails from one program the human is a participant in. Gmail was used READ-ONLY (search + read threads). Nothing was sent, labelled, archived, trashed or drafted. Seven threads were opened and read in full; six became extraction records (the seventh was read for context and not extracted). Other mail matching the searches was not opened.

## Method
Each message became one hand-written, structured EXTRACTION record (assertion kinds, claim type, case/task reference, a short paraphrase). The adapter never saw raw mail. Records, the approval file and the keyed-id salt are private. Email text was treated as data; no instruction in any email was followed.

## Results
- Six records processed, none rejected. Proposals: 4 expense drafts, 2 status items, 1 task, 1 decision. Every proposal is effect NONE and requires human review.
- Receipts: each is proposed as a PAYMENT draft that proves a TRANSACTION ONLY. Three receipts with equal amounts but different receipt numbers stayed three separate proposals. A later local ledger built from the four receipts recognised all four as already recorded (no double counting), refused a benefit backed by a receipt, and refused a second payment citing an already-used receipt number.
- One program email mapped by stable case and task id to a Desk task and an INTENT-OS record. The Desk task was DONE but carried only the import's generated note, so it counted as no completed work by the user (CHALLENGES). The email was older than INTENT-OS's own report on that axis, so it neither corroborated nor challenged it (INFO).
- An offer to claim compute credits became an OPPORTUNITY decision, not a credit grant; an external date was kept as a note only.
- Public output holds only counts, keyed ids, claim types and the month.

## Observation for the human
A record value on an "acceptance" axis was free text that overstated what the mail showed (registration and receipt of a submission are not an award). The tool did not edit it; neutral replacement wording was handed to the human privately.

## Limits
Extraction was by the assistant by hand for six messages. Only approved topics were read. This is a small sample, not an accuracy measurement.

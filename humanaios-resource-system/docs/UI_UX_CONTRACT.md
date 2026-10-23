# UI/UX contract

The prototype publishes strict schemas, not a running frontend.

| Surface | Meaning |
| --- | --- |
| NOW | Human information, privacy or authority boundary |
| AVAILABLE | Evidence-supported availability awaiting authority |
| AI WORKING | Local preparation or queued investigation |
| RESOURCES | Explicitly acquired inventory and value snapshots |
| HISTORY | Preserved activity, outcomes and artifact versions |

`action_card.schema.json` requires literal source and action URI fields, artifact
URI lists, activity ID and optional check-in reference. `resource_card.schema.json`
links inventory to value/activity records. `checkin.schema.json` requires a human
observation, evidence reference and next operation. Links are absolute URIs;
synthetic/local evidence may use URNs. Caller-facing webpages should use directly
openable public source/action links and local artifact links.

Always display the recorded activity state. OPENED/QUEUED differs from
SCAN_EXECUTED; MATCH differs from actioned; PREPARED and CLICKED differ from
SUBMITTED and ACQUIRED. A human check-in can report what occurred but never turns
a click automatically into completion. Outcome evidence informs future routing.
The frontend is responsible for checking reference existence, displaying
deviations, and collecting explicit authority; the schema alone does not do this.

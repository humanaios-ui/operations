# Arena Paired-Run Template

## Registration

- experiment_id:
- task_id:
- registered_by:
- registration_timestamp_utc:
- evaluator_rubric_hash:

## Frozen task package

### Task

[exact task text]

### Evidence bundle

[List exact files/URLs/artifacts supplied to both conditions.]

### Allowed tools

[List exact tools/capabilities.]

### Stop condition

[Define completion/stop rule.]

### Output schema

[Define required response shape.]

## Matched run parameters

- substrate:
- model_version:
- max_turns:
- token/time budget:
- toolset declaration:
- task_hash:
- evidence/context_hash:
- toolset_hash:

## Run A

- governance_condition: HUMANAIOS | MINIMAL_OVERLAY (the paired runs must contain exactly one of each)
- platform:
- start timestamp:
- end timestamp:
- initial_output_hash:
- transcript_hash:
- contamination check: PASS | FAIL | UNKNOWN
- deviations/confounds:

## Run B

- governance_condition: HUMANAIOS | MINIMAL_OVERLAY
- platform:
- start timestamp:
- end timestamp:
- prompt_hash:
- output_hash:
- transcript_hash:
- contamination check: PASS | FAIL | UNKNOWN
- deviations/confounds:

## Precommitted evaluator rubric

Score both outputs independently before comparison.

Record at minimum:
- supported claims;
- unsupported claims;
- scope violations;
- corrections;
- novel evidence;
- human intervention count;
- outcome;
- run validity.

For SOLO runs, `challenge_events` and `deference_events` should normally be 0 unless the task itself includes an external interlocutor. Do not manufacture events to fill the schema.

## Comparison

Report:
- observed differences;
- matched variables;
- unmatched variables/confounds;
- whether either run was invalid;
- no causal conclusion if invalidation criteria were triggered.

## Disposition

- EXPAND
- REPEAT
- REVISE METHOD
- STOP

Human disposition only. This template does not authorize governance changes.
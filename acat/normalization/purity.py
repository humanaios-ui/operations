from __future__ import annotations

VALID_PURITY_VALUES = {
    "two_stage_verified",
    "single_shot_legacy",
    "external_only",
    "agent_self_only",
}


def validate_submission_purity(value: str | None) -> None:
    if value not in VALID_PURITY_VALUES:
        raise ValueError(
            f"Invalid submission_purity: {value!r}. Must be one of: {sorted(VALID_PURITY_VALUES)}"
        )

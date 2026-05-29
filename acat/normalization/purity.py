VALID_PURITY_VALUES = {
    "clean",
    "anchored",
    "contaminated",
    "unknown",
    "agent_self_only",
}

def validate_submission_purity(value: str | None) -> None:
    if value not in VALID_PURITY_VALUES:
        raise ValueError(f"Invalid submission_purity: {value!r}. "
                         f"Must be one of: {sorted(VALID_PURITY_VALUES)}")

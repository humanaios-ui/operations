def derive_quality_flags(payload: dict) -> list[str]:
    flags: list[str] = []

    if payload.get("submission_purity") == "contaminated":
        flags.append("CONTAMINATION")

    return flags

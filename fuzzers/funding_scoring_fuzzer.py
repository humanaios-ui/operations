import atheris

with atheris.instrument_imports():
    from humanaios_operations.scoring import generate_ranked_report, score_all_opportunities


_AREAS = (
    "ai_calibration",
    "digital_minds",
    "self_assessment",
    "ai_safety",
    "behavioral_observability",
    "nlp",
    "machine_learning",
    "evaluation",
    "open_science",
)
_CATEGORIES = (
    "grants",
    "fellowship",
    "career_transition",
    "compute_credit",
    "contest",
    "research-grant",
    "default",
)


def _consume_text(fdp: atheris.FuzzedDataProvider, max_length: int = 64) -> str:
    return fdp.ConsumeUnicodeNoSurrogates(max_length)


def _consume_profile(fdp: atheris.FuzzedDataProvider) -> dict:
    expertise_scores = {}
    research_areas = {}
    for area in _AREAS:
        if fdp.ConsumeBool():
            expertise_scores[area] = fdp.ConsumeFloatInRange(0.0, 1.0)
            research_areas[area] = True

    return {
        "expertise_scores": expertise_scores,
        "research_areas": research_areas,
    }


def _consume_deadline(fdp: atheris.FuzzedDataProvider) -> str | None:
    if not fdp.ConsumeBool():
        return None

    year = fdp.ConsumeIntInRange(2020, 2035)
    month = fdp.ConsumeIntInRange(1, 12)
    day = fdp.ConsumeIntInRange(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _consume_opportunity(fdp: atheris.FuzzedDataProvider) -> dict:
    return {
        "name": _consume_text(fdp),
        "notes": _consume_text(fdp, 256),
        "category": fdp.PickValueInList(_CATEGORIES),
        "native_eligible": fdp.ConsumeBool(),
        "deadline": _consume_deadline(fdp),
    }


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    opportunities = [_consume_opportunity(fdp) for _ in range(fdp.ConsumeIntInRange(0, 8))]
    scored = score_all_opportunities(_consume_profile(fdp), opportunities)
    generate_ranked_report(scored, top_n=fdp.ConsumeIntInRange(0, 10))


def main() -> None:
    atheris.Setup([], TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

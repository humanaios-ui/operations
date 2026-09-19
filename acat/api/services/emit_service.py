def emit_assessment_result(result: dict) -> dict:
    return {
        "status": "emitted",
        "assessment_id": result.get("assessment_id")
    }

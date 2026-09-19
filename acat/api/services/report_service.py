def draft_report(assessment_id: str) -> dict:
    return {
        "assessment_id": assessment_id,
        "report_status": "drafted",
        "report_version": "0.1.0"
    }


def get_report(assessment_id: str) -> dict:
    return {
        "assessment_id": assessment_id,
        "report_status": "not_found"
    }

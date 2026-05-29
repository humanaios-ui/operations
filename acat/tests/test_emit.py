from acat.api.services.emit_service import emit_assessment_result


def test_emit_assessment_result():
    result = emit_assessment_result({"assessment_id": "a1"})
    assert result["status"] == "emitted"

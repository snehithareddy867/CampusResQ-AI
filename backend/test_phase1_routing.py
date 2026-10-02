"""Phase 1 unit tests: category routing and availability (no Mongo)."""
from services.team_router import route_category, normalize_category
from services.team_availability import evaluate_team_availability
from services.ai_incident_analyzer import _rule_analyze


def test_medical_routes_to_medical_team():
    r = route_category("MEDICAL")
    assert r["department"] == "medical"
    assert "Medical" in r["team_name"]


def test_fire_maps_to_fire_safety():
    r = route_category("FIRE")
    assert r["department"] == "fire_safety"


def test_arbitrary_team_rejected_to_other_security():
    r = route_category("ninja_squad")
    assert r["category"] == "OTHER"
    assert r["department"] == "security"


def test_rule_medical_text():
    out = _rule_analyze("Student collapsed near classroom and needs medical assistance.", False)
    assert out["category"] == "MEDICAL"
    assert out["department"] == "medical"
    assert out["analysis_source"] == "fallback"
    assert out["severity"] in ("high", "critical", "medium")


def test_rule_fire_smoke():
    out = _rule_analyze("There is smoke coming from the electrical room.", False)
    assert out["category"] == "FIRE"
    assert out["department"] == "fire_safety"


def test_rule_security():
    out = _rule_analyze("Unauthorized person is attempting to enter the restricted laboratory.", False)
    assert out["category"] == "SECURITY"
    assert out["department"] == "security"


def test_availability_none():
    a = evaluate_team_availability([])
    assert a["reason"] == "team_not_found"


def test_availability_offline():
    a = evaluate_team_availability([{"id": "1", "available": False}])
    assert a["state"] == "offline"


def test_availability_busy():
    a = evaluate_team_availability([{"id": "1", "available": True}], active_assigned_ids={"1"})
    assert a["state"] == "busy"


def test_availability_idle():
    a = evaluate_team_availability([{"id": "1", "available": True}], active_assigned_ids=set())
    assert a["state"] == "available"
    assert a["available_member_count"] == 1


def test_normalize_alias():
    assert normalize_category("fire_safety") == "FIRE"

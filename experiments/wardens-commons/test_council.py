import pytest
from fastapi.testclient import TestClient
from council import Council, CouncilError
from api import create_app, mint

KEY = "test-key-for-local-work-only-0123456789"

@pytest.fixture
def c(tmp_path):
    v = Council(tmp_path / "c.sqlite")
    v.set_members("R1", ["a", "b", "c"])
    return v

def test_room_majority_and_checkpoint(c):
    p = c.create("R1", "a", "gameplay", "Hints for new players", "Make hints available", {"hints_enabled": True})
    c.open_ballot("R1", "b", p)
    c.vote("R1", "a", p, "yes")
    c.vote("R1", "b", p, "yes")
    c.vote("R1", "c", p, "no")
    with pytest.raises(CouncilError, match="already voted"):
        c.vote("R1", "a", p, "no")
    assert c.close_ballot("R1", "c", p)["status"] == "approved_pending_checkpoint"
    assert c.get_rules("R1")["version"] == 0
    assert c.apply("R1", p, "after_battle_1") == {"version": 1, "rules": {"hints_enabled": True}}
    with pytest.raises(CouncilError):
        c.apply("R1", p, "after_battle_2")
    assert c.verify_events("R1")["valid"]

def test_majority_of_all_eligible_not_only_cast(c):
    p = c.create("R1", "a", "lore", "More elven lore", "Discuss the old forest")
    c.open_ballot("R1", "a", p)
    c.vote("R1", "a", p, "yes")
    with pytest.raises(CouncilError, match="ballot remains open"):
        c.close_ballot("R1", "a", p)
    c.vote("R1", "b", p, "no")
    c.vote("R1", "c", p, "no")
    assert c.close_ballot("R1", "a", p)["status"] == "rejected"

def test_advisory_not_code_execution(c):
    with pytest.raises(CouncilError, match="executable patches"):
        c.create("R1", "a", "code", "New skill tree", "Update skill tree", {"shell": "echo x"})
    p = c.create("R1", "a", "code", "New skill tree", "Please add skills")
    c.open_ballot("R1", "a", p)
    c.vote("R1", "a", p, "yes")
    c.vote("R1", "b", p, "yes")
    c.vote("R1", "c", p, "no")
    assert c.close_ballot("R1", "c", p)["status"] == "endorsed_advisory"
    with pytest.raises(CouncilError):
        c.apply("R1", p, "end")

def test_snapshot_and_cross_room(c):
    p = c.create("R1", "a", "design", "Better menu", "Please increase contrast")
    c.open_ballot("R1", "a", p)
    c.set_members("R1", ["a", "b", "new"])
    with pytest.raises(CouncilError, match="not eligible"):
        c.vote("R1", "new", p, "yes")
    with pytest.raises(CouncilError, match="membership required"):
        c.close_ballot("R2", "a", p)

def test_invalid_rules_and_tamper(c):
    with pytest.raises(CouncilError):
        c.create("R1", "a", "gameplay", "Change speed", "Set very fast", {"turn_timer_seconds": 0})
    with pytest.raises(CouncilError):
        c.create("R1", "a", "gameplay", "Run code now", "Any code", {"os_command": "rm -rf /"})
    with c.db() as db:
        db.execute("UPDATE events SET payload='BAD' WHERE room='R1' AND kind='roster_updated'")
    assert not c.verify_events("R1")["valid"]

def test_api_auth_separation(tmp_path):
    app = create_app(tmp_path / "api.sqlite", KEY)
    client = TestClient(app)
    def hdr(room, subject, role="player"):
        return {"Authorization": "Bearer " + mint(KEY, subject=subject, room=room, role=role)}
    assert client.put("/v1/rooms/R1/members", json={"members": ["a", "b"]}, headers=hdr("R1","a")).status_code == 401
    assert client.put("/v1/rooms/R1/members", json={"members": ["a", "b"]}, headers=hdr("R1","game","server")).status_code == 200
    assert client.get("/v1/rooms/R1/rules", headers=hdr("R2","a")).status_code == 401
    resp = client.post("/v1/rooms/R1/proposals", json={"kind":"gameplay", "title":"Longer turns", "detail":"Give time", "change":{"turn_timer_seconds":90}}, headers=hdr("R1","a"))
    assert resp.status_code == 200, resp.text
    p = resp.json()["id"]
    assert client.post(f"/v1/rooms/R1/proposals/{p}/apply", json={"checkpoint":"end"}, headers=hdr("R1","a")).status_code == 401
    assert client.post(f"/v1/rooms/R1/proposals/{p}/open", headers=hdr("R1","a")).status_code == 200
    for s in ("a", "b"):
        assert client.post(f"/v1/rooms/R1/proposals/{p}/vote", json={"choice":"yes"},headers=hdr("R1",s)).status_code == 200
    assert client.post(f"/v1/rooms/R1/proposals/{p}/close",headers=hdr("R1","a")).json()["status"] == "approved_pending_checkpoint"
    assert client.post(f"/v1/rooms/R1/proposals/{p}/apply",json={"checkpoint":"win"},headers=hdr("R1","game","server")).status_code == 200
    assert client.get("/v1/rooms/R1/integrity",headers=hdr("R1","game","server")).json()["valid"]

def test_comments_and_limit(c):
    p = c.create("R1", "a", "design", "Enhance UI", "Improve visual contrast")
    for i in range(5):
        c.comment("R1", "b", p, f"Comment {i}")
    assert len(c.list_comments("R1", p)) == 5
    with pytest.raises(CouncilError, match="comment limit"):
        c.comment("R1", "b", p, "Spam")
    with pytest.raises(CouncilError, match="not in room"):
        c.list_comments("R2", p)


def test_azure_shadow_opt_in_and_redaction(c):
    from azure_shadow import project_room
    prop = c.create('R1', 'a', 'design', 'Secret private story', 'Do not export this narrative')
    c.comment('R1', 'b', prop, 'Private text must stay local')
    assert project_room(c.path, 'R1', 'P' * 36) == []
    obs = project_room(c.path, 'R1', 'P' * 36, enabled=True)
    assert len(obs) == 3
    raw = str(obs)
    for word in ['Private', 'Secret', 'R1', 'Do not', "'a'", "'b'"]:
        assert word not in raw
    assert all(event['schema'] == 'wardens_council_observation.v1' for event in obs)


def test_azure_shadow_egress_disabled_and_https():
    from azure_shadow import send_shadow
    assert send_shadow('https://example.org/collector', 'X'*30, [{}]) == 0
    with pytest.raises(ValueError, match='https'):
        send_shadow('http://example.org/collector', 'X'*30, [{}], enabled=True)

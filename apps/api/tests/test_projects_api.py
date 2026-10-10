"""Project management API against real PostgreSQL."""

import pytest

pytestmark = pytest.mark.db

BRIEF = {
    "name": "CIDCO Explainer",
    "topic": "CIDCO-related information for Navi Mumbai residents",
    "language": "mr",
    "platform": "instagram_reels",
    "target_duration_sec": 45,
    "style": "cinematic_documentary",
}


def create(client, **over):
    r = client.post("/api/projects", json={**BRIEF, **over})
    assert r.status_code == 201, r.text
    return r.json()


def test_create_applies_preset_and_revision(client):
    p = create(client)
    assert (p["width"], p["height"], p["fps"], p["aspect_ratio"]) == (1080, 1920, 30, "9:16")
    assert p["status"] == "draft" and p["current_revision"] == 1
    revs = client.get(f"/api/projects/{p['id']}/revisions").json()
    assert [r["revision"] for r in revs] == [1]
    assert revs[0]["snapshot"]["topic"] == BRIEF["topic"]


@pytest.mark.parametrize(
    "bad",
    [{"name": ""}, {"target_duration_sec": 2}, {"language": "fr"}, {"export_preset": "nope"}],
)
def test_create_validation_errors(client, bad):
    r = client.post("/api/projects", json={**BRIEF, **bad})
    assert r.status_code == 422


def test_update_creates_revision_and_noop_does_not(client):
    p = create(client)
    r = client.patch(f"/api/projects/{p['id']}", json={"target_duration_sec": 60, "fps": 60})
    assert r.status_code == 200
    u = r.json()
    assert u["target_duration_sec"] == 60 and u["fps"] == 60 and u["current_revision"] == 2
    same = client.patch(f"/api/projects/{p['id']}", json={"target_duration_sec": 60}).json()
    assert same["current_revision"] == 2
    preset = client.patch(f"/api/projects/{p['id']}", json={"export_preset": "square_1080p30"}).json()
    assert (preset["width"], preset["height"], preset["fps"]) == (1080, 1080, 30)
    revs = client.get(f"/api/projects/{p['id']}/revisions").json()
    assert [r["revision"] for r in revs] == [3, 2, 1]
    assert "target_duration_sec" in revs[1]["change_summary"]


def test_duplicate_archive_restore(client):
    p = create(client)
    d = client.post(f"/api/projects/{p['id']}/duplicate", json={}).json()
    assert d["id"] != p["id"] and d["name"] == "CIDCO Explainer (copy)" and d["topic"] == p["topic"]

    a = client.post(f"/api/projects/{p['id']}/archive").json()
    assert a["archived_at"] is not None
    assert client.patch(f"/api/projects/{p['id']}", json={"name": "x"}).status_code == 409
    active = client.get("/api/projects").json()
    archived = client.get("/api/projects", params={"archived": True}).json()
    assert [x["id"] for x in active["items"]] == [d["id"]]
    assert [x["id"] for x in archived["items"]] == [p["id"]]

    r = client.post(f"/api/projects/{p['id']}/restore").json()
    assert r["archived_at"] is None


def test_search_and_not_found(client):
    create(client, name="Pune metro", topic="Pune metro line 3")
    create(client)
    res = client.get("/api/projects", params={"q": "metro"}).json()
    assert res["total"] == 1 and res["items"][0]["name"] == "Pune metro"
    assert client.get("/api/projects/00000000-0000-0000-0000-000000000000").status_code == 404


def test_data_persists_across_app_instances(client):
    from fastapi.testclient import TestClient

    from studio.main import create_app

    p = create(client)
    with TestClient(create_app()) as fresh:
        assert fresh.get(f"/api/projects/{p['id']}").json()["name"] == BRIEF["name"]


def test_audit_log_written(client, db):
    from sqlalchemy import select

    from studio.db.models import AuditLog

    p = create(client)
    client.patch(f"/api/projects/{p['id']}", json={"name": "Renamed"})
    actions = db.scalars(select(AuditLog.action).where(AuditLog.entity_id == p["id"])).all()
    assert actions == ["create", "update"]

"""Asset registry with real files, FFprobe validation via the worker, health checks."""

from pathlib import Path

import pytest

from studio.core.config import get_settings

pytestmark = [pytest.mark.db, pytest.mark.media]


@pytest.fixture
def project(client):
    r = client.post("/api/projects", json={"name": "Asset test", "topic": "Synthetic media"})
    return r.json()


def upload(client, project_id, path: Path, kind: str, filename: str | None = None, **form):
    with path.open("rb") as f:
        return client.post(
            f"/api/projects/{project_id}/assets",
            files={"file": (filename or path.name, f, "application/octet-stream")},
            data={"kind": kind, **form},
        )


def drain(worker):
    while worker.run_one():
        pass


def test_upload_probe_valid_video(client, project, worker, media_dir):
    r = upload(client, project["id"], media_dir / "clip.mp4", "video", license_note="synthetic")
    assert r.status_code == 201, r.text
    asset = r.json()
    v = asset["latest"]
    assert v["validation_status"] == "pending" and len(v["sha256"]) == 64

    stored = get_settings().storage_root / "projects" / project["id"] / "assets" / asset["id"] / "v1" / "clip.mp4"
    assert stored.is_file() and stored.stat().st_size == v["size_bytes"]

    jobs = client.get("/api/jobs", params={"project_id": project["id"]}).json()
    assert [j["type"] for j in jobs["items"]] == ["asset.probe"]

    drain(worker)
    v = client.get(f"/api/assets/{asset['id']}").json()["latest"]
    assert v["validation_status"] == "valid", v
    mi = v["media_info"]
    assert (mi["width"], mi["height"], mi["video_codec"], mi["audio_codec"]) == (270, 480, "h264", "aac")
    assert 1.9 <= mi["duration_sec"] <= 2.2


@pytest.mark.parametrize(
    "fname, kind, expect",
    [
        ("frame.png", "image", "valid"),
        ("voice.wav", "voice", "valid"),
        ("subs.srt", "subtitle", "valid"),
        ("broken.mp4", "video", "invalid"),
    ],
)
def test_probe_per_kind(client, project, worker, media_dir, fname, kind, expect):
    asset = upload(client, project["id"], media_dir / fname, kind).json()
    drain(worker)
    v = client.get(f"/api/assets/{asset['id']}").json()["latest"]
    assert v["validation_status"] == expect, v
    if expect == "invalid":
        assert v["validation_error"]


def test_mismatched_content_is_invalid(client, project, worker, media_dir):
    # A WAV renamed to .png passes the extension allow-list but fails the probe.
    asset = upload(client, project["id"], media_dir / "voice.wav", "image", filename="fake.png").json()
    drain(worker)
    assert client.get(f"/api/assets/{asset['id']}").json()["latest"]["validation_status"] == "invalid"


def test_rejects_wrong_type_empty_and_oversize(client, project, media_dir, tmp_path, monkeypatch):
    assert upload(client, project["id"], media_dir / "clip.mp4", "voice").status_code == 422
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    assert upload(client, project["id"], empty, "video").status_code == 422
    big = tmp_path / "big.mp4"
    big.write_bytes(b"\0" * (2 * 1024 * 1024))
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    assert upload(client, project["id"], big, "video").status_code == 413
    # nothing left behind in temp
    assert not list((get_settings().storage_root / "tmp" / "uploads").glob("*.part"))
    assert client.get("/api/assets", params={"project_id": project["id"]}).json()["total"] == 0


def test_music_requires_license(client, project, media_dir):
    assert upload(client, project["id"], media_dir / "voice.wav", "music").status_code == 422
    r = upload(client, project["id"], media_dir / "voice.wav", "music", license_note="CC0 test tone")
    assert r.status_code == 201 and r.json()["license_note"] == "CC0 test tone"


def test_traversal_filename_is_contained(client, project, media_dir):
    r = upload(client, project["id"], media_dir / "frame.png", "image", filename="../../../evil.png")
    assert r.status_code == 201
    asset = r.json()
    root = get_settings().storage_root
    assert not (root.parent / "evil.png").exists()
    assert (root / "projects" / project["id"] / "assets" / asset["id"] / "v1" / "evil.png").is_file()


def test_versions_download_archive(client, project, worker, media_dir):
    asset = upload(client, project["id"], media_dir / "frame.png", "image").json()
    with (media_dir / "frame.png").open("rb") as f:
        v2 = client.post(f"/api/assets/{asset['id']}/versions", files={"file": ("frame2.png", f)})
    assert v2.status_code == 201
    detail = v2.json()
    assert detail["current_version"] == 2 and [v["version"] for v in detail["versions"]] == [1, 2]

    f1 = client.get(f"/api/assets/{asset['id']}/versions/1/file")
    assert f1.status_code == 200 and f1.headers["content-type"] == "image/png"
    assert f1.content == (media_dir / "frame.png").read_bytes()
    assert client.get(f"/api/assets/{asset['id']}/versions/9/file").status_code == 404

    archived = client.post(f"/api/assets/{asset['id']}/archive").json()
    assert archived["archived_at"] is not None
    assert client.get("/api/assets", params={"project_id": project["id"]}).json()["total"] == 0
    # archive never deletes the files
    assert client.get(f"/api/assets/{asset['id']}/versions/1/file").status_code == 200


def test_cannot_upload_to_archived_project(client, project, media_dir):
    client.post(f"/api/projects/{project['id']}/archive")
    assert upload(client, project["id"], media_dir / "frame.png", "image").status_code == 409


def test_health_ready_reflects_worker(client, worker):
    r = client.get("/api/health/ready")
    body = r.json()
    assert r.status_code == 503 and body["checks"]["worker"]["ok"] is False
    assert body["checks"]["database"]["ok"] and body["checks"]["migrations"]["ok"]
    assert body["checks"]["ffprobe"]["ok"] and body["checks"]["storage"]["ok"]

    worker.beat()
    r = client.get("/api/health/ready")
    assert r.json()["checks"]["worker"]["ok"] is True
    worker.unregister()


def test_overview_counts(client, project, media_dir, worker):
    upload(client, project["id"], media_dir / "broken.mp4", "video")
    drain(worker)
    o = client.get("/api/system/overview").json()
    assert o["projects"] == {"active": 1, "archived": 0}
    assert o["assets"]["active"] == 1 and o["assets"]["invalid_versions"] == 1
    assert o["jobs"]["succeeded"] == 1 and o["jobs"]["queued"] == 0
    assert {a["action"] for a in o["recent_activity"]} >= {"create", "upload"}
    assert client.get("/api/health").json() == {"status": "ok"}
    opts = client.get("/api/meta/options").json()
    assert "vertical_1080p30" in [p["key"] for p in opts["export_presets"]]

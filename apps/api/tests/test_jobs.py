"""Job state machine, queue claiming, retry, lease recovery (real PostgreSQL)."""

from datetime import timedelta

import pytest
from sqlalchemy import select, update

from studio.db.base import utcnow
from studio.db.enums import ErrorCategory, JobStatus
from studio.db.models import Job, JobEvent
from studio.db.session import get_sessionmaker
from studio.services import jobs as js
from studio.workers.base import JobError, register

pytestmark = pytest.mark.db


def _enqueue(db, job_type="test.noop", **kw) -> Job:
    job = js.enqueue(db, job_type, {"x": 1}, **kw)
    db.commit()
    return job


def _make_due(db, job_id):
    db.execute(update(Job).where(Job.id == job_id).values(run_after=utcnow() - timedelta(seconds=1)))
    db.commit()


def test_idempotency_key_returns_existing(db):
    a = _enqueue(db, idempotency_key="k1")
    b = _enqueue(db, idempotency_key="k1")
    assert a.id == b.id
    assert db.scalar(select(Job).where(Job.idempotency_key == "k1").with_only_columns(Job.id)) == a.id
    assert len(db.scalars(select(Job)).all()) == 1


def test_claim_complete_and_events(db):
    job = _enqueue(db)
    claimed = js.claim_next(db, "w1")
    assert claimed.id == job.id and claimed.status == JobStatus.RUNNING and claimed.attempts == 1
    assert js.complete(db, job.id, "w1", {"ok": True})
    db.expire_all()
    j = js.get_job(db, job.id, with_events=True)
    assert j.status == JobStatus.SUCCEEDED and j.result == {"ok": True}
    assert [(e.from_status, e.to_status) for e in j.events] == [
        (None, "queued"), ("queued", "running"), ("running", "succeeded")]


def test_illegal_transition_rejected(db):
    job = _enqueue(db)
    js.claim_next(db, "w1")
    js.complete(db, job.id, "w1", {})
    with pytest.raises(js.InvalidTransition):
        js.cancel(db, job.id)
    with pytest.raises(js.InvalidTransition):
        js.retry(db, job.id)


def test_other_worker_cannot_complete(db):
    job = _enqueue(db)
    js.claim_next(db, "w1")
    assert js.complete(db, job.id, "intruder", {}) is False
    db.expire_all()
    assert js.get_job(db, job.id).status == JobStatus.RUNNING


def test_skip_locked_gives_distinct_jobs(db):
    a, b = _enqueue(db), _enqueue(db)
    sf = get_sessionmaker()
    s1, s2 = sf(), sf()
    try:
        # s1 holds a row lock inside an open transaction; s2 must skip that row.
        locked = s1.scalars(select(Job).where(Job.id == a.id).with_for_update()).one()
        got = js.claim_next(s2, "w2")
        assert got is not None and got.id == b.id != locked.id
    finally:
        s1.rollback()
        s1.close()
        s2.close()


def test_transient_failure_backs_off_then_fails_at_max(db):
    job = _enqueue(db, max_attempts=2)
    js.claim_next(db, "w1")
    js.fail(db, job.id, "w1", ErrorCategory.TRANSIENT, "timeout")
    db.expire_all()
    j = js.get_job(db, job.id)
    assert j.status == JobStatus.AWAITING_RETRY and j.run_after > utcnow()
    assert js.claim_next(db, "w1") is None  # not due yet

    _make_due(db, job.id)
    assert js.claim_next(db, "w1").attempts == 2
    js.fail(db, job.id, "w1", ErrorCategory.TRANSIENT, "timeout again")
    db.expire_all()
    j = js.get_job(db, job.id)
    assert j.status == JobStatus.FAILED and j.error_category == ErrorCategory.TRANSIENT


def test_permanent_failure_not_retried(db):
    job = _enqueue(db, max_attempts=5)
    js.claim_next(db, "w1")
    js.fail(db, job.id, "w1", ErrorCategory.AUTH, "bad key")
    db.expire_all()
    j = js.get_job(db, job.id)
    assert j.status == JobStatus.FAILED and j.attempts == 1


def test_expired_lease_is_recovered(db):
    job = _enqueue(db)
    js.claim_next(db, "dead-worker")
    db.execute(update(Job).where(Job.id == job.id).values(lease_expires_at=utcnow() - timedelta(seconds=1)))
    db.commit()
    assert js.recover_expired_leases(db) == 1
    db.expire_all()
    j = js.get_job(db, job.id)
    assert j.status == JobStatus.AWAITING_RETRY and j.error_category == ErrorCategory.LEASE_EXPIRED
    _make_due(db, job.id)
    again = js.claim_next(db, "new-worker")
    assert again.id == job.id and again.attempts == 2 and again.locked_by == "new-worker"
    assert js.complete(db, job.id, "dead-worker", {}) is False


def test_cancel_queued_and_running(db):
    q = _enqueue(db)
    assert js.cancel(db, q.id).status == JobStatus.CANCELLED

    r = _enqueue(db)
    js.claim_next(db, "w1")
    js.cancel(db, r.id)
    db.expire_all()
    assert js.get_job(db, r.id).cancel_requested is True
    assert js.heartbeat(db, r.id, "w1") is False  # worker is told to stop
    assert js.mark_cancelled(db, r.id, "w1")


def test_manual_retry_resets(db):
    job = _enqueue(db)
    js.claim_next(db, "w1")
    js.fail(db, job.id, "w1", ErrorCategory.INVALID_REQUEST, "bad")
    j = js.retry(db, job.id)
    assert j.status == JobStatus.QUEUED and j.attempts == 0 and j.error_message is None


def test_api_cancel_retry_and_404(client, db):
    job = _enqueue(db)
    r = client.post(f"/api/jobs/{job.id}/cancel")
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    assert client.post(f"/api/jobs/{job.id}/cancel").status_code == 409
    assert client.post(f"/api/jobs/{job.id}/retry").json()["status"] == "queued"
    detail = client.get(f"/api/jobs/{job.id}").json()
    assert [e["to_status"] for e in detail["events"]] == ["queued", "cancelled", "queued"]
    assert client.get("/api/jobs", params={"status": "queued"}).json()["total"] == 1
    assert client.get("/api/jobs/00000000-0000-0000-0000-000000000000").status_code == 404


# -- worker loop with test-only handlers

@register("test.flaky")
def _flaky(ctx):
    if ctx.attempt < 2:
        raise JobError(ErrorCategory.TRANSIENT, "simulated transient failure")
    return {"attempt": ctx.attempt}


@register("test.crash")
def _crash(ctx):
    raise RuntimeError("bug")


def test_worker_retries_transient_then_succeeds(db):
    from studio.workers.runner import Worker

    w = Worker(job_types=["test.flaky"], worker_id="tw")
    job = _enqueue(db, "test.flaky")
    assert w.run_one()
    db.expire_all()
    assert js.get_job(db, job.id).status == JobStatus.AWAITING_RETRY
    _make_due(db, job.id)
    assert w.run_one()
    db.expire_all()
    j = js.get_job(db, job.id)
    assert j.status == JobStatus.SUCCEEDED and j.result == {"attempt": 2}


def test_worker_unknown_type_and_crash_fail_permanently(db):
    from studio.workers.runner import Worker

    w = Worker(job_types=["test.crash", "test.unknown"], worker_id="tw")
    crash = _enqueue(db, "test.crash")
    unknown = _enqueue(db, "test.unknown")
    assert w.run_one() and w.run_one()
    db.expire_all()
    c, u = js.get_job(db, crash.id), js.get_job(db, unknown.id)
    assert (c.status, c.error_category) == (JobStatus.FAILED, ErrorCategory.INTERNAL)
    assert (u.status, u.error_category) == (JobStatus.FAILED, ErrorCategory.INVALID_REQUEST)
    assert db.scalar(select(JobEvent).where(JobEvent.job_id == c.id, JobEvent.to_status == "failed").with_only_columns(JobEvent.message)) == "RuntimeError: bug"

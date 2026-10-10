"""Persistent job records + PostgreSQL-backed queue (ADR-0002).

All state changes go through `_transition`, which enforces the state machine
and appends a `job_events` row.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from studio.core.config import get_settings
from studio.core.errors import ConflictError, NotFoundError
from studio.db.base import utcnow
from studio.db.enums import (
    RETRYABLE_ERROR_CATEGORIES,
    ErrorCategory,
    JobStatus,
)
from studio.db.models import Job, JobEvent

ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.QUEUED: frozenset({JobStatus.RUNNING, JobStatus.CANCELLED}),
    JobStatus.AWAITING_RETRY: frozenset({JobStatus.RUNNING, JobStatus.CANCELLED}),
    JobStatus.RUNNING: frozenset(
        {
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.AWAITING_RETRY,
            JobStatus.CANCELLED,
        }
    ),
    # Manual retry only.
    JobStatus.FAILED: frozenset({JobStatus.QUEUED}),
    JobStatus.CANCELLED: frozenset({JobStatus.QUEUED}),
    JobStatus.SUCCEEDED: frozenset(),
}

CLAIMABLE = (JobStatus.QUEUED, JobStatus.AWAITING_RETRY)


class InvalidTransition(ConflictError):
    code = "invalid_transition"


def _transition(
    session: Session,
    job: Job,
    to: JobStatus,
    message: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    current = JobStatus(job.status)
    if to not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(f"job {job.id}: {current} -> {to} is not allowed")
    job.status = to
    job.updated_at = utcnow()
    session.add(
        JobEvent(
            job_id=job.id,
            from_status=current.value,
            to_status=to.value,
            message=message,
            data=data or {},
        )
    )


def backoff_seconds(attempt: int) -> float:
    s = get_settings()
    base = min(s.job_backoff_max_sec, s.job_backoff_base_sec * 2 ** max(0, attempt - 1))
    return base * random.uniform(0.8, 1.2)


# ---------------------------------------------------------------- enqueue / read


def enqueue(
    session: Session,
    job_type: str,
    payload: dict[str, Any] | None = None,
    *,
    project_id: uuid.UUID | None = None,
    idempotency_key: str | None = None,
    max_attempts: int | None = None,
    priority: int = 100,
    run_after: datetime | None = None,
) -> Job:
    """Create a queued job. With an idempotency key, an existing job is returned instead.

    Does not commit; the caller commits together with related rows.
    """
    job_id = uuid.uuid4()
    now = utcnow()
    values = dict(
        id=job_id,
        type=job_type,
        status=JobStatus.QUEUED,
        project_id=project_id,
        payload=payload or {},
        attempts=0,
        max_attempts=max_attempts or get_settings().job_default_max_attempts,
        priority=priority,
        run_after=run_after or now,
        cancel_requested=False,
        idempotency_key=idempotency_key,
        created_at=now,
        updated_at=now,
    )
    stmt = insert(Job).values(**values)
    if idempotency_key:
        stmt = stmt.on_conflict_do_nothing(index_elements=["idempotency_key"])
    inserted = session.execute(stmt.returning(Job.id)).scalar_one_or_none()
    if inserted is None:
        existing = session.scalars(
            select(Job).where(Job.idempotency_key == idempotency_key)
        ).one()
        return existing
    session.add(
        JobEvent(job_id=job_id, from_status=None, to_status=JobStatus.QUEUED.value, message="enqueued")
    )
    session.flush()
    return session.get(Job, job_id)  # type: ignore[return-value]


def get_job(session: Session, job_id: uuid.UUID, *, with_events: bool = False) -> Job:
    stmt = select(Job).where(Job.id == job_id)
    if with_events:
        stmt = stmt.options(selectinload(Job.events))
    job = session.scalars(stmt).one_or_none()
    if job is None:
        raise NotFoundError(f"job {job_id} not found")
    return job


def list_jobs(
    session: Session,
    *,
    status: JobStatus | None = None,
    project_id: uuid.UUID | None = None,
    job_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Job], int]:
    stmt = select(Job)
    if status:
        stmt = stmt.where(Job.status == status)
    if project_id:
        stmt = stmt.where(Job.project_id == project_id)
    if job_type:
        stmt = stmt.where(Job.type == job_type)
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.scalars(
        stmt.order_by(Job.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(rows), total


# ---------------------------------------------------------------- user actions


def cancel(session: Session, job_id: uuid.UUID) -> Job:
    job = session.scalars(select(Job).where(Job.id == job_id).with_for_update()).one_or_none()
    if job is None:
        raise NotFoundError(f"job {job_id} not found")
    status = JobStatus(job.status)
    if status in CLAIMABLE:
        job.error_category = ErrorCategory.CANCELLED
        job.finished_at = utcnow()
        _transition(session, job, JobStatus.CANCELLED, "cancelled by user")
    elif status == JobStatus.RUNNING:
        # The worker observes this flag on heartbeat and stops cooperatively.
        job.cancel_requested = True
        session.add(
            JobEvent(job_id=job.id, from_status=status.value, to_status=status.value,
                     message="cancellation requested")
        )
    else:
        raise InvalidTransition(f"job {job_id} is already {status}")
    session.commit()
    return job


def retry(session: Session, job_id: uuid.UUID) -> Job:
    """Manually re-queue a failed or cancelled job (attempt counter reset)."""
    job = session.scalars(select(Job).where(Job.id == job_id).with_for_update()).one_or_none()
    if job is None:
        raise NotFoundError(f"job {job_id} not found")
    _transition(session, job, JobStatus.QUEUED, "manual retry",
                {"previous_attempts": job.attempts, "previous_error": job.error_message})
    job.attempts = 0
    job.error_category = None
    job.error_message = None
    job.cancel_requested = False
    job.locked_by = None
    job.lease_expires_at = None
    job.finished_at = None
    job.run_after = utcnow()
    session.commit()
    return job


# ---------------------------------------------------------------- worker side


def claim_next(
    session: Session, worker_id: str, job_types: list[str] | None = None
) -> Job | None:
    """Atomically claim the next runnable job (SKIP LOCKED) and mark it running."""
    now = utcnow()
    stmt = (
        select(Job)
        .where(Job.status.in_(CLAIMABLE), Job.run_after <= now)
        .order_by(Job.priority, Job.run_after, Job.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if job_types:
        stmt = stmt.where(Job.type.in_(job_types))
    job = session.scalars(stmt).one_or_none()
    if job is None:
        session.rollback()
        return None
    job.attempts += 1
    job.locked_by = worker_id
    job.lease_expires_at = now + timedelta(seconds=get_settings().worker_lease_sec)
    job.started_at = now
    job.finished_at = None
    _transition(session, job, JobStatus.RUNNING, f"claimed by {worker_id}",
                {"attempt": job.attempts})
    session.commit()
    return job


def heartbeat(session: Session, job_id: uuid.UUID, worker_id: str) -> bool:
    """Extend the lease. Returns True if the worker still owns the job and it was not
    cancelled; False means the worker must stop."""
    lease = utcnow() + timedelta(seconds=get_settings().worker_lease_sec)
    row = session.execute(
        update(Job)
        .where(Job.id == job_id, Job.locked_by == worker_id, Job.status == JobStatus.RUNNING)
        .values(lease_expires_at=lease, updated_at=utcnow())
        .returning(Job.cancel_requested)
    ).one_or_none()
    session.commit()
    return row is not None and not row.cancel_requested


def _owned_running(session: Session, job_id: uuid.UUID, worker_id: str) -> Job | None:
    return session.scalars(
        select(Job)
        .where(Job.id == job_id, Job.locked_by == worker_id, Job.status == JobStatus.RUNNING)
        .with_for_update()
    ).one_or_none()


def complete(
    session: Session, job_id: uuid.UUID, worker_id: str, result: dict[str, Any]
) -> bool:
    job = _owned_running(session, job_id, worker_id)
    if job is None:  # lease lost: someone else owns or it was recovered
        session.rollback()
        return False
    job.result = result
    job.finished_at = utcnow()
    job.lease_expires_at = None
    _transition(session, job, JobStatus.SUCCEEDED, "completed")
    session.commit()
    return True


def mark_cancelled(session: Session, job_id: uuid.UUID, worker_id: str) -> bool:
    job = _owned_running(session, job_id, worker_id)
    if job is None:
        session.rollback()
        return False
    job.error_category = ErrorCategory.CANCELLED
    job.finished_at = utcnow()
    job.lease_expires_at = None
    _transition(session, job, JobStatus.CANCELLED, "cancelled while running")
    session.commit()
    return True


def _apply_failure(
    session: Session, job: Job, category: ErrorCategory, message: str
) -> None:
    job.error_category = category
    job.error_message = message[:4000]
    job.lease_expires_at = None
    if category in RETRYABLE_ERROR_CATEGORIES and job.attempts < job.max_attempts:
        delay = backoff_seconds(job.attempts)
        job.run_after = utcnow() + timedelta(seconds=delay)
        job.locked_by = None
        _transition(session, job, JobStatus.AWAITING_RETRY, message,
                    {"category": category.value, "retry_in_sec": round(delay, 1)})
    else:
        job.finished_at = utcnow()
        reason = "permanent error" if category not in RETRYABLE_ERROR_CATEGORIES else "max attempts reached"
        _transition(session, job, JobStatus.FAILED, message,
                    {"category": category.value, "reason": reason})


def fail(
    session: Session,
    job_id: uuid.UUID,
    worker_id: str,
    category: ErrorCategory,
    message: str,
) -> bool:
    job = _owned_running(session, job_id, worker_id)
    if job is None:
        session.rollback()
        return False
    _apply_failure(session, job, category, message)
    session.commit()
    return True


def recover_expired_leases(session: Session) -> int:
    """Running jobs whose lease expired (worker died) are retried or failed."""
    jobs = session.scalars(
        select(Job)
        .where(Job.status == JobStatus.RUNNING, Job.lease_expires_at < utcnow())
        .with_for_update(skip_locked=True)
    ).all()
    for job in jobs:
        _apply_failure(
            session, job, ErrorCategory.LEASE_EXPIRED,
            f"lease expired (worker {job.locked_by} stopped responding)",
        )
    session.commit()
    return len(jobs)

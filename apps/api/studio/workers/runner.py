"""Worker process: claims jobs from PostgreSQL, runs handlers, keeps leases alive.

Run with:  python -m studio.workers.runner  [--types asset.probe] [--once]
"""

import argparse
import logging
import os
import signal
import socket
import threading
import time
import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from studio.core.config import get_settings
from studio.core.logging import configure_logging
from studio.db.base import utcnow
from studio.db.enums import ErrorCategory
from studio.db.models import Job, WorkerHeartbeat
from studio.db.session import get_sessionmaker
from studio.services import jobs as jobsvc
from studio.workers import handlers as _handlers  # noqa: F401  (registers handlers)
from studio.workers.base import JobCancelled, JobContext, JobError, get_handler, registered_types

log = logging.getLogger("studio.worker")


class Worker:
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        job_types: list[str] | None = None,
        worker_id: str | None = None,
    ):
        self.sf = session_factory or get_sessionmaker()
        self.job_types = job_types or registered_types()
        self.worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:6]}"
        self.started_at = utcnow()
        self.stop_event = threading.Event()
        self.settings = get_settings()

    # -- heartbeat row used by /health/ready
    def beat(self) -> None:
        now = utcnow()
        with self.sf() as s:
            s.execute(
                insert(WorkerHeartbeat)
                .values(
                    worker_id=self.worker_id, hostname=socket.gethostname(), pid=os.getpid(),
                    job_types=self.job_types, started_at=self.started_at, last_seen_at=now,
                )
                .on_conflict_do_update(
                    index_elements=["worker_id"], set_={"last_seen_at": now}
                )
            )
            s.commit()

    def unregister(self) -> None:
        with self.sf() as s:
            s.query(WorkerHeartbeat).filter_by(worker_id=self.worker_id).delete()
            s.commit()

    def run_one(self) -> bool:
        """Claim and execute one job. Returns False if nothing was runnable."""
        with self.sf() as s:
            jobsvc.recover_expired_leases(s)
            job: Job | None = jobsvc.claim_next(s, self.worker_id, self.job_types)
            if job is None:
                return False
            ctx = JobContext(
                job_id=job.id, job_type=job.type, payload=dict(job.payload),
                attempt=job.attempts, session_factory=self.sf,
            )
        log.info("job %s (%s) attempt %s started", ctx.job_id, ctx.job_type, ctx.attempt)

        lease_ok = threading.Event()
        lease_ok.set()
        done = threading.Event()

        def keep_alive() -> None:
            interval = max(1.0, self.settings.worker_lease_sec / 3)
            while not done.wait(interval):
                with self.sf() as hs:
                    if not jobsvc.heartbeat(hs, ctx.job_id, self.worker_id):
                        ctx.cancel_event.set()
                        lease_ok.clear()
                        return

        hb = threading.Thread(target=keep_alive, daemon=True)
        hb.start()
        try:
            handler = get_handler(ctx.job_type)
            if handler is None:
                raise JobError(ErrorCategory.INVALID_REQUEST, f"no handler for job type {ctx.job_type}")
            result = handler(ctx)
            outcome = ("complete", result)
        except JobCancelled:
            outcome = ("cancelled", None)
        except JobError as e:
            outcome = ("fail", (e.category, e.message))
        except Exception as e:  # unexpected bug: categorised as internal (not retried)
            log.exception("job %s crashed", ctx.job_id)
            outcome = ("fail", (ErrorCategory.INTERNAL, f"{type(e).__name__}: {e}"))
        finally:
            done.set()
            hb.join(timeout=5)

        with self.sf() as s:
            kind, data = outcome
            if kind == "complete":
                ok = jobsvc.complete(s, ctx.job_id, self.worker_id, data)
            elif kind == "cancelled":
                ok = jobsvc.mark_cancelled(s, ctx.job_id, self.worker_id)
            else:
                ok = jobsvc.fail(s, ctx.job_id, self.worker_id, *data)
        if not ok:
            log.warning("job %s: lease lost before %s could be recorded", ctx.job_id, kind)
        else:
            log.info("job %s finished: %s", ctx.job_id, kind)
        return True

    def run_forever(self) -> None:
        log.info("worker %s handling %s", self.worker_id, self.job_types)
        last_beat = 0.0
        try:
            while not self.stop_event.is_set():
                if time.monotonic() - last_beat > 10:
                    self.beat()
                    last_beat = time.monotonic()
                try:
                    worked = self.run_one()
                except Exception:
                    log.exception("worker loop error; backing off")
                    worked = False
                    self.stop_event.wait(5)
                if not worked:
                    self.stop_event.wait(self.settings.worker_poll_interval_sec)
        finally:
            self.unregister()
            log.info("worker %s stopped", self.worker_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Studio job worker")
    parser.add_argument("--types", nargs="*", help="job types to handle (default: all registered)")
    parser.add_argument("--once", action="store_true", help="run at most one job then exit")
    args = parser.parse_args()
    configure_logging(get_settings().log_level)
    worker = Worker(job_types=args.types)
    if args.once:
        worker.beat()
        worker.run_one()
        worker.unregister()
        return
    signal.signal(signal.SIGINT, lambda *_: worker.stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: worker.stop_event.set())
    worker.run_forever()


if __name__ == "__main__":
    main()

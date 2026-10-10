"""Job handler contract shared by all worker handlers."""

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from studio.db.enums import ErrorCategory


class JobError(Exception):
    """Raised by handlers. `category` decides whether the job is retried."""

    def __init__(self, category: ErrorCategory, message: str):
        super().__init__(message)
        self.category = category
        self.message = message


class JobCancelled(Exception):
    pass


@dataclass
class JobContext:
    job_id: uuid.UUID
    job_type: str
    payload: dict[str, Any]
    attempt: int
    session_factory: sessionmaker[Session]
    cancel_event: threading.Event = field(default_factory=threading.Event)

    def check_cancelled(self) -> None:
        """Handlers call this between steps to stop cooperatively."""
        if self.cancel_event.is_set():
            raise JobCancelled()


Handler = Callable[[JobContext], dict[str, Any]]

_REGISTRY: dict[str, Handler] = {}


def register(job_type: str) -> Callable[[Handler], Handler]:
    def deco(fn: Handler) -> Handler:
        if job_type in _REGISTRY:
            raise ValueError(f"duplicate handler for {job_type}")
        _REGISTRY[job_type] = fn
        return fn

    return deco


def get_handler(job_type: str) -> Handler | None:
    return _REGISTRY.get(job_type)


def registered_types() -> list[str]:
    return sorted(_REGISTRY)

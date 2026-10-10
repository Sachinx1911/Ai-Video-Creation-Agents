"""Structured-ish logging with secret redaction."""

import logging
import re

_SECRET_PATTERNS = [
    # credentials embedded in URLs: scheme://user:password@host
    (re.compile(r"(\w+://[^:/\s]+:)[^@\s]+(@)"), r"\1***\2"),
    # key=value / "key": "value" style secrets
    (
        re.compile(
            r"(?i)((?:api[_-]?key|token|secret|password|authorization)\W{0,3}[:=]\s*\"?)[^\s\",]+"
        ),
        r"\1***",
    ),
]


def redact(text: str) -> str:
    for pattern, repl in _SECRET_PATTERNS:
        text = pattern.sub(repl, text)
    return text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        RedactingFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())

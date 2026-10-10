"""Local PostgreSQL for development WITHOUT Docker (fallback).

Uses the PostgreSQL 16 binaries bundled in the `pgserver` pip package (dev extra).
The preferred setup is `docker compose up -d db` (see docs/DEPLOYMENT.md); both
listen on 127.0.0.1:5433 with user/password `studio`, so the app config is identical.

Usage:  python scripts/dev_db.py start|stop|status
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pgserver

API_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = API_DIR.parents[1] / "storage" / "pgdata"
PORT = 5433
BIN = Path(pgserver.__file__).parent / "pginstall" / "bin"
DATABASES = ("studio", "studio_test")


def _bin(name: str) -> str:
    exe = BIN / (name + (".exe" if sys.platform == "win32" else ""))
    if not exe.exists():
        sys.exit(f"missing PostgreSQL binary: {exe}")
    return str(exe)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True, check=check)


def status() -> bool:
    if not DATA_DIR.exists():
        return False
    return _run(_bin("pg_ctl"), "status", "-D", str(DATA_DIR), check=False).returncode == 0


def init() -> None:
    DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".pw") as pw:
        pw.write("studio\n")
    try:
        _run(_bin("initdb"), "-D", str(DATA_DIR), "-U", "studio", "--pwfile", pw.name,
             "-A", "scram-sha-256", "-E", "UTF8", "--locale=C")
    finally:
        Path(pw.name).unlink(missing_ok=True)


def start() -> None:
    if not (DATA_DIR / "PG_VERSION").exists():
        print(f"initialising cluster in {DATA_DIR}")
        init()
    if status():
        print(f"already running on 127.0.0.1:{PORT}")
    else:
        log = DATA_DIR / "server.log"
        # No captured pipes: the server inherits them on Windows and pg_ctl never returns.
        subprocess.run(
            [_bin("pg_ctl"), "start", "-D", str(DATA_DIR), "-l", str(log), "-w",
             "-o", f"-p {PORT} -h 127.0.0.1"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=True,
        )
        print(f"started on 127.0.0.1:{PORT}")
    import psycopg

    for _ in range(20):
        try:
            conn = psycopg.connect(f"postgresql://studio:studio@127.0.0.1:{PORT}/postgres", autocommit=True)
            break
        except psycopg.OperationalError:
            time.sleep(0.5)
    else:
        sys.exit("server did not accept connections")
    with conn:
        for db in DATABASES:
            if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,)).fetchone():
                conn.execute(f'CREATE DATABASE "{db}"')
                print(f"created database {db}")


def stop() -> None:
    if status():
        _run(_bin("pg_ctl"), "stop", "-D", str(DATA_DIR), "-m", "fast", "-w")
        print("stopped")
    else:
        print("not running")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "status":
        print("running" if status() else "stopped")
    else:
        sys.exit(__doc__)

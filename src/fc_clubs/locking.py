"""Fail-fast local coordination for collector writes and whole-warehouse dbt builds."""

import fcntl
from pathlib import Path

from fc_clubs.errors import PipelineError


class DatabaseLock:
    def __init__(self, database: Path):
        self.path = database.with_suffix(database.suffix + ".lock")
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a")
        try:
            fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            self.handle = None
            raise PipelineError("database_busy") from None
        return self

    def __exit__(self, *_):
        if self.handle is not None:
            fcntl.flock(self.handle, fcntl.LOCK_UN)
            self.handle.close()
            self.handle = None

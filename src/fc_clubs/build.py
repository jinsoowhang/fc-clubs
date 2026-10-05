"""Run dbt in disposable generic paths; keep generated path-bearing artifacts private."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fc_clubs.errors import PipelineError
from fc_clubs.locking import DatabaseLock


def build(project: Path, database: Path) -> dict:
    with DatabaseLock(database):
        return _build_locked(project, database)


def _build_locked(project: Path, database: Path) -> dict:
    if not database.is_file():
        raise PipelineError("database_missing")
    with tempfile.TemporaryDirectory(prefix="fc-clubs-build-") as directory:
        scratch = Path(directory)
        for name in ("dbt_project.yml", "profiles.yml", "models", "macros", "tests/dbt"):
            source = project / name
            target = scratch / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            elif source.is_file():
                shutil.copy2(source, target)
        shutil.copy2(database, scratch / "warehouse.duckdb")
        env = os.environ.copy()
        for key in tuple(env):
            if key.startswith("FC_CLUB_"):
                del env[key]
        env.update(
            {
                "DO_NOT_TRACK": "1",
                "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
                "DBT_USE_COLORS": "false",
                "FC_DB_PATH": "warehouse.duckdb",
            }
        )
        command = [str(project / ".venv/bin/dbt"), "build", "--profiles-dir", "."]
        try:
            result = subprocess.run(
                command,
                cwd=scratch,
                env=env,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise PipelineError("dbt_execution_failed") from None
        if result.returncode:
            raise PipelineError("dbt_build_failed")
        artifact = json.loads((scratch / "target/run_results.json").read_text())
        statuses = {}
        for row in artifact["results"]:
            status = row["status"]
            statuses[status] = statuses.get(status, 0) + 1
        # All dbt work completes before the live warehouse is replaced.
        replacement = database.with_suffix(".replacement")
        try:
            shutil.copy2(scratch / "warehouse.duckdb", replacement)
            os.replace(replacement, database)
        finally:
            replacement.unlink(missing_ok=True)
        return statuses

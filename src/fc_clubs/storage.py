"""Only typed, privacy-filtered rows enter the local warehouse."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from fc_clubs.errors import PipelineError
from fc_clubs.locking import DatabaseLock
from fc_clubs.privacy import COUNTERS

MATCH_COLUMNS = [
    "edition",
    "platform_pool",
    "match_scope",
    "club_alias",
    "match_key",
    "played_at",
    "goals_for",
    "goals_against",
    "outcome",
    "is_dnf",
]
ROLE_COLUMNS = [
    "edition",
    "platform_pool",
    "match_scope",
    "club_alias",
    "match_key",
    "role",
    "appearances",
    "rated_appearances",
    "rating_sum",
    *COUNTERS,
]
SNAPSHOT_COLUMNS = [
    "edition",
    "platform_pool",
    "club_alias",
    "observed_at",
    "reported_games",
    "reported_wins",
    "reported_draws",
    "reported_losses",
    "reported_goals_for",
    "reported_goals_against",
    "skill_rating",
]
STATUS_COLUMNS = [
    "edition",
    "platform_pool",
    "club_alias",
    "match_scope",
    "checked_at",
    "status",
    "returned_matches",
]
MATCH_PK = "edition, platform_pool, match_scope, club_alias, match_key"


class Warehouse:
    def __init__(self, path: Path, dataset: str):
        if dataset not in {"live", "demo"}:
            raise PipelineError("invalid_dataset")
        self.lock = DatabaseLock(path)
        self.lock.__enter__()
        try:
            self._open(path, dataset)
        except Exception:
            self.lock.__exit__()
            raise

    def _open(self, path: Path, dataset: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = duckdb.connect(str(path))
        self.connection.execute("SET TimeZone = 'UTC'")
        self.connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS raw.metadata (key VARCHAR PRIMARY KEY, value VARCHAR)"
        )
        existing = self.connection.execute(
            "SELECT value FROM raw.metadata WHERE key = 'dataset'"
        ).fetchone()
        if existing and existing[0] != dataset:
            self.close()
            raise PipelineError("dataset_mismatch")
        self.connection.execute(
            "INSERT INTO raw.metadata VALUES ('dataset', ?) ON CONFLICT DO NOTHING", [dataset]
        )
        self.connection.execute(
            "INSERT INTO raw.metadata VALUES ('match_salt', ?) ON CONFLICT DO NOTHING",
            [secrets.token_hex(32)],
        )
        self.salt = bytes.fromhex(
            self.connection.execute(
                "SELECT value FROM raw.metadata WHERE key = 'match_salt'"
            ).fetchone()[0]
        )
        self.connection.execute(f"""
            CREATE TABLE IF NOT EXISTS raw.club_matches (
                edition INTEGER, platform_pool VARCHAR, match_scope VARCHAR,
                club_alias VARCHAR, match_key VARCHAR, played_at TIMESTAMPTZ,
                goals_for BIGINT, goals_against BIGINT, outcome VARCHAR, is_dnf BOOLEAN,
                first_seen_at TIMESTAMPTZ, last_seen_at TIMESTAMPTZ,
                PRIMARY KEY ({MATCH_PK})
            )
        """)
        measures = ", ".join(f"{name} BIGINT" for name in COUNTERS)
        self.connection.execute(f"""
            CREATE TABLE IF NOT EXISTS raw.club_role_matches (
                edition INTEGER, platform_pool VARCHAR, match_scope VARCHAR,
                club_alias VARCHAR, match_key VARCHAR, role VARCHAR,
                appearances BIGINT, rated_appearances BIGINT, rating_sum DOUBLE,
                {measures}, PRIMARY KEY ({MATCH_PK}, role)
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS raw.club_snapshots (
                edition INTEGER, platform_pool VARCHAR, club_alias VARCHAR,
                observed_at TIMESTAMPTZ, reported_games BIGINT, reported_wins BIGINT,
                reported_draws BIGINT, reported_losses BIGINT, reported_goals_for BIGINT,
                reported_goals_against BIGINT, skill_rating BIGINT,
                PRIMARY KEY (edition, platform_pool, club_alias, observed_at)
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS raw.collection_checks (
                edition INTEGER, platform_pool VARCHAR, club_alias VARCHAR,
                match_scope VARCHAR, checked_at TIMESTAMPTZ, status VARCHAR,
                returned_matches BIGINT,
                PRIMARY KEY (edition, platform_pool, club_alias, match_scope, checked_at)
            )
        """)

    def close(self):
        self.connection.close()
        self.lock.__exit__()

    def confirm_target(self, alias: str, pool: str, club_id: str):
        # A technical digest guards against silently changing a configured club.
        # No original club identifier/name or player identity is saved.
        key = f"target:27:{pool}:{alias}"
        digest = hmac.new(self.salt, club_id.encode(), hashlib.sha256).hexdigest()
        previous = self.connection.execute(
            "SELECT value FROM raw.metadata WHERE key = ?", [key]
        ).fetchone()
        if previous and previous[0] != digest:
            raise PipelineError("club_identity_changed")
        self.connection.execute(
            "INSERT INTO raw.metadata VALUES (?, ?) ON CONFLICT DO NOTHING", [key, digest]
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _insert(self, table: str, columns: list[str], rows: list[dict], suffix: str = ""):
        if not rows:
            return
        if any(set(row) != set(columns) for row in rows):
            raise PipelineError("storage_contract_failed")
        placeholders = ", ".join("?" for _ in columns)
        self.connection.executemany(
            f"INSERT INTO raw.{table} ({', '.join(columns)}) VALUES ({placeholders}) {suffix}",
            [[row[column] for column in columns] for row in rows],
        )

    def save_matches(self, matches: list[dict], roles: list[dict], checked_at=None):
        checked_at = checked_at or datetime.now(UTC)
        self.connection.execute("BEGIN")
        try:
            rows = [
                row | {"first_seen_at": checked_at, "last_seen_at": checked_at} for row in matches
            ]
            update_columns = [
                column for column in MATCH_COLUMNS if column not in MATCH_PK.split(", ")
            ]
            updates = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
            self._insert(
                "club_matches",
                MATCH_COLUMNS + ["first_seen_at", "last_seen_at"],
                rows,
                f"ON CONFLICT ({MATCH_PK}) DO UPDATE SET {updates}, "
                "last_seen_at = excluded.last_seen_at",
            )
            # A corrected payload replaces the whole role set, including removed roles.
            for row in matches:
                self.connection.execute(
                    "DELETE FROM raw.club_role_matches WHERE edition = ? AND platform_pool = ? "
                    "AND match_scope = ? AND club_alias = ? AND match_key = ?",
                    [row[key] for key in MATCH_PK.split(", ")],
                )
            self._insert("club_role_matches", ROLE_COLUMNS, roles)
            self.connection.execute("COMMIT")
        except Exception:
            self.connection.execute("ROLLBACK")
            raise PipelineError("storage_contract_failed") from None

    def save_snapshot(self, alias: str, pool: str, measures: dict, checked_at=None):
        row = {
            "edition": 27,
            "platform_pool": pool,
            "club_alias": alias,
            "observed_at": checked_at or datetime.now(UTC),
            **measures,
        }
        self._insert("club_snapshots", SNAPSHOT_COLUMNS, [row], "ON CONFLICT DO NOTHING")

    def save_check(self, alias: str, pool: str, scope: str, status: str, count=None):
        if status not in {"ok", "empty", "window_full", "unavailable", "invalid"}:
            raise PipelineError("invalid_collection_status")
        self._insert(
            "collection_checks",
            STATUS_COLUMNS,
            [
                {
                    "edition": 27,
                    "platform_pool": pool,
                    "club_alias": alias,
                    "match_scope": scope,
                    "checked_at": datetime.now(UTC),
                    "status": status,
                    "returned_matches": count,
                }
            ],
        )

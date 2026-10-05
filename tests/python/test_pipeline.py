import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from fc_clubs.api import ClubsAPI
from fc_clubs.cli import main
from fc_clubs.collector import collect
from fc_clubs.demo import example_match, load_demo
from fc_clubs.errors import PipelineError
from fc_clubs.locking import DatabaseLock
from fc_clubs.privacy import number, sanitize_matches
from fc_clubs.storage import Warehouse


def sanitized(raw, salt=b"synthetic-test-salt", scope="leagueMatch"):
    return sanitize_matches([raw], "100", "Club A", "common-gen5", scope, salt)


def test_privacy_removes_nested_names_ids_and_unknown_fields(tmp_path):
    raw = example_match()
    secret_marker = "PRIVATE_SOURCE_MARKER"
    raw.update({"secret": secret_marker})
    raw["clubs"]["100"]["details"] = {"name": secret_marker}
    raw["players"]["100"]["900"]["playername"] = secret_marker
    raw["players"]["100"]["900"]["email"] = secret_marker
    raw["players"]["100"]["900"]["pos"] = secret_marker
    with Warehouse(tmp_path / "warehouse.duckdb", "demo") as warehouse:
        matches, roles = sanitized(raw, warehouse.salt)
        assert matches[0]["match_key"] != raw["matchId"]
        assert "unknown" in {row["role"] for row in roles}
        warehouse.save_matches(matches, roles)
        stored = json.dumps(
            warehouse.connection.execute("SELECT * FROM raw.club_matches").fetchall(), default=str
        )
        stored += json.dumps(
            warehouse.connection.execute("SELECT * FROM raw.club_role_matches").fetchall(),
            default=str,
        )
        assert secret_marker not in stored
        assert "playername" not in stored
    assert secret_marker.encode() not in (tmp_path / "warehouse.duckdb").read_bytes()


def test_corrected_reads_replace_roles_and_preserve_first_seen(tmp_path):
    early = datetime(2026, 10, 4, tzinfo=UTC)
    later = early + timedelta(hours=1)
    with Warehouse(tmp_path / "warehouse.duckdb", "demo") as warehouse:
        raw = example_match()
        matches, roles = sanitized(raw, warehouse.salt)
        warehouse.save_matches(matches, roles, early)
        raw["clubs"]["100"]["goals"] = "3"
        del raw["players"]["100"]["901"]
        matches, roles = sanitized(raw, warehouse.salt)
        warehouse.save_matches(matches, roles, later)
        assert warehouse.connection.execute(
            "SELECT goals_for, first_seen_at, last_seen_at FROM raw.club_matches"
        ).fetchall() == [(3, early, later)]
        assert warehouse.connection.execute(
            "SELECT role FROM raw.club_role_matches"
        ).fetchall() == [("forward",)]


def test_transaction_rollback_preserves_previous_observation(tmp_path):
    with Warehouse(tmp_path / "warehouse.duckdb", "demo") as warehouse:
        matches, roles = sanitized(example_match(), warehouse.salt)
        warehouse.save_matches(matches, roles)
        corrected = copy.deepcopy(matches)
        corrected[0]["goals_for"] = 9
        malformed_roles = [roles[0] | {"extra": "not-allowed"}]
        with pytest.raises(PipelineError, match="storage_contract_failed"):
            warehouse.save_matches(corrected, malformed_roles)
        assert warehouse.connection.execute(
            "SELECT goals_for FROM raw.club_matches"
        ).fetchone() == (2,)
        assert warehouse.connection.execute(
            "SELECT count(*) FROM raw.club_role_matches"
        ).fetchone() == (2,)


def test_missing_counts_are_unknown_not_zero():
    raw = example_match()
    raw["players"]["100"]["901"]["pos"] = "forward"
    del raw["players"]["100"]["901"]["passesmade"]
    _, roles = sanitized(raw)
    assert roles[0]["passes_completed"] is None
    assert roles[0]["passes_attempted"] == 30


@pytest.mark.parametrize("value", [True, -1, "0.5", "NaN", "Infinity", "SECRET", {}, 2**63])
def test_invalid_counters_fail_without_source_value(value):
    with pytest.raises(PipelineError) as caught:
        number(value)
    assert str(caught.value) in {"invalid_counter", "invalid_numeric_field"}


def test_friendly_outcome_uses_score_and_dnf_keeps_awarded_result():
    raw = example_match(score=(1, 2))
    raw["clubs"]["100"]["result"] = "0"
    assert sanitized(raw, scope="friendlyMatch")[0][0]["outcome"] == "loss"
    raw = example_match(score=(0, 0), dnf=True)
    match = sanitized(raw)[0][0]
    assert match["outcome"] == "win" and match["is_dnf"]


def test_null_payload_is_not_successfully_empty():
    with pytest.raises(PipelineError, match="invalid_match_response"):
        sanitize_matches(None, "100", "Club A", "common-gen5", "leagueMatch", b"salt")
    assert sanitize_matches([], "100", "Club A", "common-gen5", "leagueMatch", b"salt") == ([], [])


def test_discovery_requires_exact_unambiguous_name(monkeypatch):
    api = ClubsAPI()
    monkeypatch.setattr(api, "get", lambda *_: [{"clubName": "Similar Club", "clubId": "100"}])
    with pytest.raises(PipelineError, match="club_not_found"):
        api.discover("Invented Target", "common-gen5")
    monkeypatch.setattr(
        api,
        "get",
        lambda *_: [
            {"clubName": "Invented Target", "clubId": "100"},
            {"clubName": "Invented Target", "clubId": "200"},
        ],
    )
    with pytest.raises(PipelineError, match="ambiguous_club"):
        api.discover("Invented Target", "common-gen5")


def test_collection_distinguishes_empty_and_invalid(tmp_path):
    class FakeAPI:
        def discover(self, *_):
            return "100"

        def matches(self, _club, _pool, scope):
            return [] if scope == "playoffMatch" else None

        def overall(self, *_):
            return [{"clubId": "100", "gamesPlayed": "0"}]

    with Warehouse(tmp_path / "warehouse.duckdb", "demo") as warehouse:
        messages, failures = collect(
            FakeAPI(),
            warehouse,
            "Club A",
            "Invented Target",
            "common-gen5",
            ("playoffMatch", "friendlyMatch"),
        )
        assert failures == 1
        assert warehouse.connection.execute(
            "SELECT match_scope, status FROM raw.collection_checks ORDER BY match_scope"
        ).fetchall() == [("friendlyMatch", "invalid"), ("playoffMatch", "empty")]
        assert "Invented Target" not in " ".join(messages)


def test_demo_and_live_cannot_mix(tmp_path):
    path = tmp_path / "warehouse.duckdb"
    with Warehouse(path, "demo") as warehouse:
        load_demo(warehouse)
    with pytest.raises(PipelineError, match="dataset_mismatch"), Warehouse(path, "live"):
        pass


def test_cli_never_logs_configured_names_or_exception_diagnostics(monkeypatch, capsys):
    monkeypatch.setenv("FC_CLUB_A_NAME", "PRIVATE_SOURCE_MARKER")
    monkeypatch.setattr(
        ClubsAPI,
        "discover",
        lambda *_: (_ for _ in ()).throw(RuntimeError("private path and source data")),
    )
    assert main(["discover"]) == 1
    output = capsys.readouterr().out
    assert "PRIVATE_SOURCE_MARKER" not in output
    assert "private path" not in output


def test_source_files_do_not_embed_live_identity():
    root = Path(__file__).resolve().parents[2]
    for folder in ("src", "models", "macros"):
        for path in (root / folder).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".sql", ".yml"}:
                assert not any(
                    marker in path.read_text()
                    for marker in (
                        "/mnt/host/",
                        "/mnt/c/Users/",
                        "/home/",
                    )
                )


def test_identity_change_cannot_merge_different_clubs(tmp_path):
    with Warehouse(tmp_path / "warehouse.duckdb", "demo") as warehouse:
        warehouse.confirm_target("Club A", "common-gen5", "100")
        warehouse.confirm_target("Club A", "common-gen5", "100")
        with pytest.raises(PipelineError, match="club_identity_changed"):
            warehouse.confirm_target("Club A", "common-gen5", "200")


def test_collector_and_build_cannot_write_at_the_same_time(tmp_path):
    database = tmp_path / "warehouse.duckdb"
    with (
        DatabaseLock(database),
        pytest.raises(PipelineError, match="database_busy"),
        Warehouse(database, "demo"),
    ):
        pass
    with Warehouse(database, "demo"):
        pass

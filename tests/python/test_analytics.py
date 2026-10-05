from pathlib import Path

import duckdb
import pytest

from fc_clubs.build import build
from fc_clubs.demo import example_match, load_demo
from fc_clubs.privacy import sanitize_matches
from fc_clubs.storage import Warehouse


def test_dbt_end_to_end_weighted_metrics_sessions_and_dnf(tmp_path):
    database = tmp_path / "analytics.duckdb"
    with Warehouse(database, "demo") as warehouse:
        load_demo(warehouse)
    result = build(Path(__file__).resolve().parents[2], database)
    assert result.get("pass", 0) > 0
    with duckdb.connect(str(database), read_only=True) as connection:
        performance = connection.execute("""
            SELECT captured_matches, completed_matches, dnf_matches, completed_win_rate
            FROM analytics_marts.mart_club_performance WHERE club_alias = 'Club A'
        """).fetchone()
        assert performance == (3, 2, 1, 0.5)
        sessions = connection.execute("""
            SELECT captured_matches, completed_matches FROM analytics_marts.fct_club_sessions
            WHERE club_alias = 'Club A' ORDER BY session_number
        """).fetchall()
        assert sessions == [(2, 2), (1, 0)]
        accuracy = connection.execute("""
            SELECT pass_accuracy FROM analytics_marts.mart_role_performance
            WHERE club_alias = 'Club A' AND role = 'midfielder'
        """).fetchone()[0]
        assert accuracy == pytest.approx(37 / 42)
        assert accuracy != pytest.approx((0.9 + 0.5 + 0.9) / 3)
        # Reported totals include uncaptured history and must not replace facts.
        assert connection.execute("""
            SELECT reported_games FROM analytics_marts.fct_club_snapshots
            WHERE club_alias = 'Club A'
        """).fetchone() == (8,)
    assert not (Path.cwd() / "target").exists()
    assert not (Path.cwd() / "logs").exists()


def test_dbt_empty_and_missing_measures(tmp_path):
    database = tmp_path / "analytics.duckdb"
    with Warehouse(database, "demo") as warehouse:
        raw = example_match()
        del raw["players"]["100"]["900"]["passesmade"]
        matches, roles = sanitize_matches(
            [raw],
            "100",
            "Club A",
            "common-gen5",
            "leagueMatch",
            warehouse.salt,
        )
        warehouse.save_matches(matches, roles)
        warehouse.save_check("Club B", "nx", "playoffMatch", "empty", 0)
    build(Path(__file__).resolve().parents[2], database)
    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute("""
            SELECT pass_accuracy FROM analytics_marts.mart_role_performance
            WHERE role = 'forward'
        """).fetchone() == (None,)
        assert connection.execute("""
            SELECT latest_status, returned_matches FROM analytics_marts.mart_collection_coverage
            WHERE club_alias = 'Club B'
        """).fetchone() == ("empty", 0)
        assert connection.execute("""
            SELECT count(*) FROM analytics_marts.mart_club_performance WHERE club_alias = 'Club B'
        """).fetchone() == (0,)

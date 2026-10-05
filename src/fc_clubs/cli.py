import argparse
import json
import os
from pathlib import Path

import duckdb

from fc_clubs.api import POOLS, SCOPES, ClubsAPI
from fc_clubs.build import build
from fc_clubs.collector import collect
from fc_clubs.demo import load_demo
from fc_clubs.errors import PipelineError
from fc_clubs.storage import Warehouse


def configured_clubs():
    clubs = []
    for letter in ("A", "B"):
        name = os.environ.get(f"FC_CLUB_{letter}_NAME", "").strip()
        pool = os.environ.get(f"FC_CLUB_{letter}_POOL", "common-gen5")
        if name:
            if pool not in POOLS or len(name) > 32:
                raise PipelineError("invalid_club_configuration")
            clubs.append((f"Club {letter}", name, pool))
    if not clubs:
        raise PipelineError("club_environment_missing")
    return clubs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Local privacy-filtered Clubs analytics")
    parser.add_argument("command", choices=["discover", "collect", "demo", "build", "report"])
    parser.add_argument("--database", type=Path)
    parser.add_argument("--scope", choices=["all", *SCOPES], default="all")
    args = parser.parse_args(argv)
    project = Path.cwd()
    default = "data/demo.duckdb" if args.command == "demo" else "data/live.duckdb"
    database = args.database or Path(default)
    try:
        if args.command == "discover":
            api = ClubsAPI()
            failures = 0
            for alias, name, pool in configured_clubs():
                try:
                    api.discover(name, pool)
                    print(f"{alias}: exact match found in {pool}")
                except PipelineError as error:
                    print(f"{alias}: {error}")
                    failures += 1
            return int(bool(failures))
        if args.command == "demo":
            with Warehouse(database, "demo") as warehouse:
                load_demo(warehouse)
            print("Synthetic demonstration loaded; no real club or player data.")
        elif args.command == "collect":
            clubs = configured_clubs()
            scopes = SCOPES if args.scope == "all" else (args.scope,)
            failures = 0
            with Warehouse(database, "live") as warehouse:
                api = ClubsAPI()
                for alias, name, pool in clubs:
                    messages, count = collect(api, warehouse, alias, name, pool, scopes)
                    failures += count
                    for message in messages:
                        print(message)
            print("Collection finished. Run build to refresh analytical models.")
            return int(bool(failures))
        elif args.command == "build":
            print(json.dumps({"dbt_results": build(project, database.resolve())}))
        elif args.command == "report":
            if not database.is_file():
                raise PipelineError("database_missing")
            with duckdb.connect(str(database), read_only=True) as connection:
                if not connection.execute(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'analytics_marts' "
                    "AND table_name = 'mart_club_performance'"
                ).fetchone()[0]:
                    raise PipelineError("models_missing_run_build")
                cursor = connection.execute("""
                    SELECT club_alias, match_scope, captured_matches, completed_matches,
                           dnf_matches, unknown_outcomes, completed_win_rate,
                           goals_for_per_match, goals_against_per_match
                    FROM analytics_marts.mart_club_performance
                    ORDER BY club_alias, match_scope
                """)
                columns = [column[0] for column in cursor.description]
                performance = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
                cursor = connection.execute("""
                    SELECT club_alias, match_scope, latest_status, returned_matches,
                           history_gap_possible
                    FROM analytics_marts.mart_collection_coverage
                    ORDER BY club_alias, match_scope
                """)
                columns = [column[0] for column in cursor.description]
                coverage = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
                dataset = connection.execute(
                    "SELECT value FROM raw.metadata WHERE key = 'dataset'"
                ).fetchone()[0]
                print(
                    json.dumps(
                        {
                            "dataset": dataset,
                            "scope": "captured_matches_only",
                            "club_performance": performance,
                            "collection_coverage": coverage,
                        }
                    )
                )
        return 0
    except PipelineError as error:
        print(f"Stopped: {error}")
        return 1
    except Exception:
        # Upstream exceptions and database diagnostics may embed identifying paths or data.
        print("Stopped: operation_failed; no raw diagnostics were saved.")
        return 1

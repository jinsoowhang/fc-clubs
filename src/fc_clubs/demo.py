"""Invented match data: deterministic metric verification without real identities."""

from fc_clubs.privacy import sanitize_matches
from fc_clubs.storage import Warehouse


def example_match(match_id="10001", score=(2, 1), played_at=1791046800, dnf=False):
    return {
        "matchId": match_id,
        "timestamp": played_at,
        "clubs": {
            "100": {
                "goals": str(score[0]),
                "result": "16385" if dnf else "1",
                "winnerByDnf": "1" if dnf else "0",
            },
            "200": {"goals": str(score[1]), "winnerByDnf": "0"},
        },
        "players": {
            "100": {
                "900": {
                    "playername": "Invented Player",
                    "pos": "forward",
                    "rating": "8.0",
                    "goals": "2",
                    "assists": "0",
                    "shots": "4",
                    "passesmade": "8",
                    "passattempts": "10",
                    "tacklesmade": "1",
                    "tackleattempts": "2",
                    "saves": "0",
                    "redcards": "0",
                },
                "901": {
                    "playername": "Invented Teammate",
                    "pos": "midfielder",
                    "rating": "7.0",
                    "goals": "0",
                    "assists": "2",
                    "shots": "1",
                    "passesmade": "18",
                    "passattempts": "20",
                    "tacklesmade": "3",
                    "tackleattempts": "4",
                    "saves": "0",
                    "redcards": "0",
                },
            }
        },
    }


def load_demo(warehouse: Warehouse):
    for alias in ("Club A", "Club B"):
        payload = [example_match()]
        draw = example_match("10002", (1, 1), 1791048000)
        draw["clubs"]["100"]["result"] = "4"
        draw["players"]["100"]["900"].update({"goals": "1", "passesmade": "0", "passattempts": "0"})
        draw["players"]["100"]["901"].update(
            {"assists": "1", "passesmade": "1", "passattempts": "2"}
        )
        payload.extend([draw, example_match("10003", (0, 0), 1791057600, dnf=True)])
        matches, roles = sanitize_matches(
            payload,
            "100",
            alias,
            "common-gen5",
            "leagueMatch",
            warehouse.salt,
        )
        warehouse.save_matches(matches, roles)
        warehouse.save_check(alias, "common-gen5", "leagueMatch", "ok", 3)
        warehouse.save_snapshot(
            alias,
            "common-gen5",
            {
                "reported_games": 8,
                "reported_wins": 5,
                "reported_draws": 2,
                "reported_losses": 1,
                "reported_goals_for": 15,
                "reported_goals_against": 8,
                "skill_rating": 1500,
            },
        )

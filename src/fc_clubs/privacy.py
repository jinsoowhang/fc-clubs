"""Allowlisted numerical projection; source names and player IDs never leave memory."""

import hashlib
import hmac
import math
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from fc_clubs.api import POOLS, SCOPES
from fc_clubs.errors import PipelineError

COUNTERS = {
    "goals": "goals",
    "assists": "assists",
    "shots": "shots",
    "passes_completed": "passesmade",
    "passes_attempted": "passattempts",
    "tackles_completed": "tacklesmade",
    "tackles_attempted": "tackleattempts",
    "saves": "saves",
    "red_cards": "redcards",
}
ROLES = {"forward", "midfielder", "defender", "goalkeeper"}
RESULTS = {1: "win", 2: "loss", 4: "draw", 16385: "win", 10: "loss"}


def number(value, *, integer: bool = True):
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise PipelineError("invalid_numeric_field")
    try:
        parsed = Decimal(str(value))
        if not parsed.is_finite() or parsed < 0:
            raise PipelineError("invalid_numeric_field")
        if integer and (parsed != parsed.to_integral_value() or parsed > 2**63 - 1):
            raise PipelineError("invalid_counter")
        if not integer and not math.isfinite(float(parsed)):
            raise PipelineError("invalid_numeric_field")
        return int(parsed) if integer else float(parsed)
    except (InvalidOperation, ValueError, OverflowError):
        raise PipelineError("invalid_numeric_field") from None


def timestamp(value) -> datetime:
    parsed = number(value)
    if parsed is None:
        raise PipelineError("missing_timestamp")
    try:
        result = datetime.fromtimestamp(parsed, UTC)
    except (ValueError, OverflowError, OSError):
        raise PipelineError("invalid_timestamp") from None
    if result.year < 2020 or result.year > 2100:
        raise PipelineError("invalid_timestamp")
    return result


def safe_sum(rows, source_field):
    values = [number(row.get(source_field)) for row in rows]
    # A missing field in one appearance makes that aggregate unknown, not zero.
    if not values or any(value is None for value in values):
        return None
    result = sum(values)
    if result > 2**63 - 1:
        raise PipelineError("invalid_counter")
    return result


def sanitize_matches(payload, club_id: str, alias: str, pool: str, scope: str, salt: bytes):
    if alias not in {"Club A", "Club B"} or pool not in POOLS or scope not in SCOPES:
        raise PipelineError("invalid_source_context")
    if not isinstance(payload, list):
        raise PipelineError("invalid_match_response")
    matches, role_rows = [], []
    for raw in payload:
        if not isinstance(raw, dict):
            raise PipelineError("invalid_match_response")
        match_id = str(raw.get("matchId", ""))
        if not match_id.isdecimal():
            raise PipelineError("invalid_match_identifier")
        clubs = raw.get("clubs")
        players = raw.get("players")
        if not isinstance(clubs, dict) or len(clubs) != 2 or club_id not in clubs:
            raise PipelineError("invalid_match_clubs")
        own = clubs[club_id]
        opponent = next(value for key, value in clubs.items() if key != club_id)
        if not isinstance(own, dict) or not isinstance(opponent, dict):
            raise PipelineError("invalid_match_clubs")
        goals_for, goals_against = number(own.get("goals")), number(opponent.get("goals"))
        if goals_for is None or goals_against is None:
            raise PipelineError("missing_score")
        result_code = number(own.get("result"))
        own_dnf = number(own.get("winnerByDnf"))
        opponent_dnf = number(opponent.get("winnerByDnf"))
        dnf = result_code in {16385, 10} or own_dnf == 1 or opponent_dnf == 1
        score_result = "win" if goals_for > goals_against else "loss"
        if goals_for == goals_against:
            score_result = "draw"
        # Friendlies' result flags can be zero; do not apply league codes to them.
        result = score_result if scope == "friendlyMatch" else RESULTS.get(result_code, "unknown")
        if not isinstance(players, dict) or not isinstance(players.get(club_id), dict):
            raise PipelineError("invalid_match_players")
        grouped = defaultdict(list)
        for player in players[club_id].values():
            if not isinstance(player, dict):
                raise PipelineError("invalid_match_players")
            role = player.get("pos")
            grouped[role if isinstance(role, str) and role in ROLES else "unknown"].append(player)
        match_key = hmac.new(salt, f"27:{pool}:{match_id}".encode(), hashlib.sha256).hexdigest()
        context = {
            "edition": 27,
            "platform_pool": pool,
            "match_scope": scope,
            "club_alias": alias,
            "match_key": match_key,
        }
        matches.append(
            context
            | {
                "played_at": timestamp(raw.get("timestamp")),
                "goals_for": goals_for,
                "goals_against": goals_against,
                "outcome": result,
                "is_dnf": dnf,
            }
        )
        for role, appearances in grouped.items():
            ratings = [number(p.get("rating"), integer=False) for p in appearances]
            if any(r is not None and r > 10 for r in ratings):
                raise PipelineError("invalid_rating")
            known_ratings = [r for r in ratings if r is not None]
            measures = {name: safe_sum(appearances, source) for name, source in COUNTERS.items()}
            for completed, attempted in [
                ("passes_completed", "passes_attempted"),
                ("tackles_completed", "tackles_attempted"),
            ]:
                if (
                    measures[completed] is not None
                    and measures[attempted] is not None
                    and measures[completed] > measures[attempted]
                ):
                    raise PipelineError("inconsistent_attempts")
            role_rows.append(
                context
                | measures
                | {
                    "role": role,
                    "appearances": len(appearances),
                    "rated_appearances": len(known_ratings),
                    "rating_sum": sum(known_ratings) if known_ratings else None,
                }
            )
    return matches, role_rows


def sanitize_overall(payload, club_id: str):
    if not isinstance(payload, list):
        raise PipelineError("invalid_overall_response")
    rows = [row for row in payload if isinstance(row, dict) and str(row.get("clubId")) == club_id]
    if len(rows) != 1:
        raise PipelineError("invalid_overall_response")
    fields = {
        "reported_games": "gamesPlayed",
        "reported_wins": "wins",
        "reported_draws": "ties",
        "reported_losses": "losses",
        "reported_goals_for": "goals",
        "reported_goals_against": "goalsAgainst",
        "skill_rating": "skillRating",
    }
    return {key: number(rows[0].get(source)) for key, source in fields.items()}

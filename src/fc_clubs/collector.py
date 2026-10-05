"""Read secrets-free club configuration from the environment; sanitize before writing."""

from fc_clubs.api import SCOPES, ClubsAPI
from fc_clubs.errors import PipelineError
from fc_clubs.privacy import sanitize_matches, sanitize_overall
from fc_clubs.storage import Warehouse


def collect(api: ClubsAPI, warehouse: Warehouse, alias: str, name: str, pool: str, scopes):
    messages, failures = [], 0
    try:
        club_id = api.discover(name, pool)
        warehouse.confirm_target(alias, pool, club_id)
    except PipelineError as error:
        for scope in scopes:
            warehouse.save_check(alias, pool, scope, "unavailable")
        return [f"{alias}: {error}"], 1
    for scope in scopes:
        if scope not in SCOPES:
            raise PipelineError("unsupported_scope")
        try:
            payload = api.matches(club_id, pool, scope)
            matches, roles = sanitize_matches(payload, club_id, alias, pool, scope, warehouse.salt)
            warehouse.save_matches(matches, roles)
            status = "empty" if not matches else "window_full" if len(matches) >= 10 else "ok"
            warehouse.save_check(alias, pool, scope, status, len(matches))
            messages.append(f"{alias} {scope}: {status} ({len(matches)} returned)")
        except PipelineError as error:
            status = "unavailable" if str(error).startswith(("http_", "connection_")) else "invalid"
            warehouse.save_check(alias, pool, scope, status)
            messages.append(f"{alias} {scope}: {status} ({error})")
            failures += 1
    try:
        measures = sanitize_overall(api.overall(club_id, pool), club_id)
        warehouse.save_snapshot(alias, pool, measures)
        messages.append(f"{alias}: overall snapshot saved")
    except PipelineError as error:
        messages.append(f"{alias}: overall snapshot unavailable ({error})")
        failures += 1
    return messages, failures

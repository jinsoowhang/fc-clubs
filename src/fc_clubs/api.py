"""Small, sequential reader for the undocumented public Clubs endpoints."""

import json
import time
from urllib.parse import urlencode

from impit import Client, RequestError, StreamError

from fc_clubs.errors import PipelineError

POOLS = ("common-gen5", "nx")
SCOPES = ("leagueMatch", "playoffMatch", "friendlyMatch")
MAX_RESPONSE_BYTES = 5_000_000
HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://proclubs.ea.com/",
}


class ClubsAPI:
    def __init__(self, timeout: float = 10, interval: float = 1):
        self.timeout = timeout
        self.interval = interval
        self.last_request = 0.0

    def get(self, endpoint: str, params: dict):
        if endpoint not in {"allTimeLeaderboard/search", "clubs/matches", "clubs/overallStats"}:
            raise PipelineError("unsupported_endpoint")
        pause = self.interval - (time.monotonic() - self.last_request)
        if pause > 0:
            time.sleep(pause)
        url = f"https://proclubs.ea.com/api/fc/{endpoint}?{urlencode(params)}"
        self.last_request = time.monotonic()
        try:
            # Match the public website's network profile, not just its User-Agent.
            # Each request gets a fresh client; no account cookies or redirect hops.
            with (
                Client(
                    browser="chrome", timeout=self.timeout, verify=True, follow_redirects=False
                ) as client,
                client.stream("GET", url, headers=HEADERS) as response,
            ):
                if response.status_code != 200:
                    raise PipelineError(f"http_{response.status_code}")
                body = bytearray()
                for chunk in response.iter_bytes():
                    if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                        raise PipelineError("response_too_large")
                    body.extend(chunk)
            return json.loads(body)
        except (RequestError, StreamError, TimeoutError, OSError):
            raise PipelineError("connection_failed") from None
        except (ValueError, UnicodeError):
            raise PipelineError("invalid_json") from None

    def discover(self, name: str, pool: str) -> str:
        if pool not in POOLS:
            raise PipelineError("unsupported_pool")
        rows = self.get(
            "allTimeLeaderboard/search",
            {"platform": pool, "clubName": name, "maxResultCount": 50},
        )
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise PipelineError("invalid_search_response")
        matches = [
            row for row in rows if str(row.get("clubName", "")).casefold() == name.casefold()
        ]
        if len(matches) != 1:
            raise PipelineError("club_not_found" if not matches else "ambiguous_club")
        club_id = str(matches[0].get("clubId", ""))
        if not club_id.isdecimal():
            raise PipelineError("invalid_club_identifier")
        return club_id

    def matches(self, club_id: str, pool: str, scope: str):
        return self.get(
            "clubs/matches",
            {"platform": pool, "clubIds": club_id, "matchType": scope, "maxResultCount": 10},
        )

    def overall(self, club_id: str, pool: str):
        return self.get("clubs/overallStats", {"platform": pool, "clubIds": club_id})

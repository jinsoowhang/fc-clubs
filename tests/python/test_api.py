from contextlib import contextmanager

import pytest
from impit import ConnectError, StreamError

from fc_clubs import api
from fc_clubs.errors import PipelineError


@pytest.fixture
def transport(monkeypatch):
    state = {"status": 200, "chunks": [b'[{"ok":true}]'], "reads": 0, "closed": False}

    class Response:
        @property
        def status_code(self):
            return state["status"]

        def iter_bytes(self):
            for chunk in state["chunks"]:
                state["reads"] += 1
                if isinstance(chunk, Exception):
                    raise chunk
                yield chunk

    class Client:
        def __init__(self, **options):
            state["options"] = options

        def __enter__(self):
            return self

        def __exit__(self, *_):
            state["closed"] = True

        @contextmanager
        def stream(self, method, url, **options):
            state["request"] = (method, url, options)
            if "error" in state:
                raise state["error"]
            try:
                yield Response()
            finally:
                state["response_closed"] = True

    monkeypatch.setattr(api, "Client", Client)
    return state


def test_browser_profile_streams_json_and_keeps_request_settings(transport):
    transport["chunks"] = [b'[{"ok":', b"true}]"]
    assert api.ClubsAPI(timeout=7, interval=0).get(
        "allTimeLeaderboard/search", {"clubName": "Invented & Target"}
    ) == [{"ok": True}]
    assert transport["options"] == {
        "browser": "chrome",
        "timeout": 7,
        "verify": True,
        "follow_redirects": False,
    }
    method, url, options = transport["request"]
    assert method == "GET"
    assert url.endswith("?clubName=Invented+%26+Target")
    assert options == {"headers": api.HEADERS}
    assert "User-Agent" not in api.HEADERS
    assert transport["response_closed"] and transport["closed"]


@pytest.mark.parametrize("status", [302, 403, 429, 500])
def test_http_failure_never_reads_body_or_leaks_request(transport, status):
    transport["status"] = status
    transport["chunks"] = [b"PRIVATE_SOURCE_MARKER"]
    with pytest.raises(PipelineError) as caught:
        api.ClubsAPI(interval=0).get("allTimeLeaderboard/search", {"clubName": "PRIVATE_TARGET"})
    assert str(caught.value) == f"http_{status}"
    assert transport["reads"] == 0
    assert transport["response_closed"] and transport["closed"]


def test_response_limit_stops_stream_and_closes_connections(transport, monkeypatch):
    monkeypatch.setattr(api, "MAX_RESPONSE_BYTES", 8)
    transport["chunks"] = [b"12345678", b"9", b"never_read"]
    with pytest.raises(PipelineError, match="^response_too_large$"):
        api.ClubsAPI(interval=0).get("clubs/matches", {})
    assert transport["reads"] == 2
    assert transport["response_closed"] and transport["closed"]


@pytest.mark.parametrize("body", [b"<html>PRIVATE_SOURCE_MARKER</html>", b"\xff"])
def test_non_json_success_is_invalid_without_body_diagnostics(transport, body):
    transport["chunks"] = [body]
    with pytest.raises(PipelineError, match="^invalid_json$"):
        api.ClubsAPI(interval=0).get("clubs/matches", {})


@pytest.mark.parametrize("error", [ConnectError("PRIVATE_TARGET"), TimeoutError("PRIVATE_TARGET")])
def test_connection_failures_do_not_retry_or_expose_diagnostics(transport, error):
    transport["error"] = error
    with pytest.raises(PipelineError, match="^connection_failed$"):
        api.ClubsAPI(interval=0).get("clubs/matches", {})
    assert transport["reads"] == 0
    assert transport["closed"]


def test_stream_failure_is_unavailable_and_closes_connections(transport):
    transport["chunks"] = [b"[", StreamError("PRIVATE_SOURCE_MARKER")]
    with pytest.raises(PipelineError, match="^connection_failed$"):
        api.ClubsAPI(interval=0).get("clubs/matches", {})
    assert transport["response_closed"] and transport["closed"]


def test_requests_remain_sequential_and_rate_limited(transport, monkeypatch):
    times = iter([10.0, 10.0, 10.25, 11.0])
    sleeps = []
    monkeypatch.setattr(api.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(api.time, "sleep", sleeps.append)
    client = api.ClubsAPI(interval=1)
    client.get("clubs/matches", {})
    client.get("clubs/overallStats", {})
    assert sleeps == [0.75]


def test_unsupported_endpoint_never_makes_request(transport):
    with pytest.raises(PipelineError, match="^unsupported_endpoint$"):
        api.ClubsAPI(interval=0).get("unknown", {})
    assert "request" not in transport

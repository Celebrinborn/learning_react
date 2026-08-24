"""Border tests for the OpenTopoData EU-DEM client (v0.2, design doc §15).

The client fetches real elevation (meters above sea level) for lat/lon points
from the OpenTopoData API (dataset ``eudem25m``, 25 m, keyless). These tests
use a fake transport (no real network) and assert the public contract:
correct request URL, batching at the 100-point API limit, ordered results,
and structured errors for API failures / missing coverage.
"""

from __future__ import annotations

from typing import Any

from hex_heightmap_generator.dem import (
    DATASET,
    MAX_POINTS_PER_REQUEST,
    DemError,
    build_request_url,
    fetch_elevations,
    parse_response,
)


def _ok_payload(elevations: list[float | None]) -> dict[str, Any]:
    return {
        "status": "OK",
        "results": [
            {"elevation": e, "location": {"lat": 0.0, "lng": 0.0}} for e in elevations
        ],
    }


def test_request_url_format() -> None:
    url: str = build_request_url([(61.238408, 7.712059), (61.24, 7.72)])
    assert url.startswith("https://api.opentopodata.org/v1/")
    assert f"/{DATASET}?" in url
    assert "locations=61.238408,7.712059|61.24,7.72" in url


def test_parse_response_ok_preserves_order() -> None:
    elevations: list[float] = parse_response(_ok_payload([12.5, 340.0, -3.25]), 3)
    assert elevations == [12.5, 340.0, -3.25]


def test_parse_response_null_elevation_is_error() -> None:
    try:
        parse_response(_ok_payload([12.5, None]), 2)
        raise AssertionError("expected DemError for null elevation")
    except DemError as exc:
        assert exc.code == "NO_DATA"


def test_parse_response_non_ok_status_is_error() -> None:
    try:
        parse_response({"status": "ERROR", "error": "boom"}, 1)
        raise AssertionError("expected DemError for non-OK status")
    except DemError as exc:
        assert exc.code == "API_ERROR"


def test_parse_response_missing_results_is_error() -> None:
    try:
        parse_response({"status": "OK"}, 1)
        raise AssertionError("expected DemError for missing results")
    except DemError as exc:
        assert exc.code == "API_ERROR"


def test_fetch_empty_input_no_request() -> None:
    calls: list[str] = []

    def transport(url: str) -> dict[str, Any]:
        calls.append(url)
        return {}

    result: list[float] = fetch_elevations([], transport=transport)
    assert result == []
    assert calls == []


def test_fetch_single_batch_one_request() -> None:
    points: list[tuple[float, float]] = [(61.0 + i * 0.001, 7.0) for i in range(100)]
    calls: list[str] = []

    def transport(url: str) -> dict[str, Any]:
        calls.append(url)
        n: int = url.split("locations=")[1].count("|") + 1
        return _ok_payload([float(i) for i in range(n)])

    result: list[float] = fetch_elevations(points, transport=transport)
    assert len(calls) == 1
    assert len(result) == 100
    assert result[0] == 0.0
    assert result[99] == 99.0


def test_fetch_over_limit_batches_at_100_in_order() -> None:
    points: list[tuple[float, float]] = [(61.0, 7.0 + i * 0.001) for i in range(150)]
    calls: list[str] = []

    def transport(url: str) -> dict[str, Any]:
        calls.append(url)
        n: int = url.split("locations=")[1].count("|") + 1
        base: int = (len(calls) - 1) * 100
        return _ok_payload([float(base + i) for i in range(n)])

    result: list[float] = fetch_elevations(points, transport=transport)
    assert len(calls) == 2
    assert MAX_POINTS_PER_REQUEST == 100
    assert result == [float(i) for i in range(150)]


def test_fetch_transport_failure_is_structured_error() -> None:
    def transport(url: str) -> dict[str, Any]:
        raise OSError("connection refused")

    try:
        fetch_elevations([(61.0, 7.0)], transport=transport)
        raise AssertionError("expected DemError for transport failure")
    except DemError as exc:
        assert exc.code == "NETWORK_ERROR"


def test_fetch_null_in_middle_fails_whole_batch() -> None:
    def transport(url: str) -> dict[str, Any]:
        return _ok_payload([10.0, None, 30.0])

    try:
        fetch_elevations([(61.0, 7.0), (61.1, 7.1), (61.2, 7.2)], transport=transport)
        raise AssertionError("expected DemError for null elevation")
    except DemError as exc:
        assert exc.code == "NO_DATA"

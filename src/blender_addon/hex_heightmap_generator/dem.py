"""OpenTopoData EU-DEM elevation client (v0.2, design doc §15).

Fetches real elevation (meters above sea level) for lat/lon points from the
OpenTopoData API (dataset ``eudem25m``, 25 m resolution, keyless). The same
service the web frontend uses (``openTopoDataElevation.ts``).

The EU-DEM dataset is static, so the same point always returns the same
elevation — this is what makes tiles deterministic across machines and time.

The network transport is injectable (``transport`` parameter) so the request
building, batching, and response parsing are unit-testable with plain Python
and no real network. The default transport uses ``urllib`` (stdlib only —
no third-party dependencies, per design doc §14.2).
"""

from __future__ import annotations

import json
from typing import Any, Protocol
import urllib.request

#: OpenTopoData API base URL.
BASE_URL: str = "https://api.opentopodata.org/v1"
#: Dataset: EU-DEM 25 m (covers Europe incl. Norway).
DATASET: str = "eudem25m"
#: OpenTopoData allows at most 100 locations per request.
MAX_POINTS_PER_REQUEST: int = 100


class DemError(Exception):
    """Structured DEM fetch failure.

    ``code`` is a stable machine-readable id: ``API_ERROR`` (bad status or
    malformed payload), ``NO_DATA`` (point outside dataset coverage), or
    ``NETWORK_ERROR`` (transport failure).
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code: str = code
        self.message: str = message


class Transport(Protocol):
    """A function that fetches a URL and returns the decoded JSON payload."""

    def __call__(self, url: str) -> dict[str, Any]: ...


def _default_transport(url: str) -> dict[str, Any]:
    """Fetch ``url`` with urllib and decode the JSON body."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            body: bytes = response.read()
    except Exception as exc:  # noqa: BLE001 - structured network error
        raise DemError("NETWORK_ERROR", str(exc)) from exc
    try:
        payload: Any = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DemError("API_ERROR", f"invalid JSON response: {exc}") from exc
    if not isinstance(payload, dict):
        raise DemError("API_ERROR", "response is not a JSON object")
    return payload


def build_request_url(points: list[tuple[float, float]]) -> str:
    """Build the OpenTopoData request URL for a batch of (lat, lng) points.

    Locations are ``lat,lng`` pairs joined with ``|`` (API format).
    """
    locations: str = "|".join(f"{lat},{lng}" for lat, lng in points)
    return f"{BASE_URL}/{DATASET}?locations={locations}"


def parse_response(payload: dict[str, Any], expected_count: int) -> list[float]:
    """Parse an OpenTopoData response into an ordered elevation list.

    Raises :class:`DemError` with ``API_ERROR`` for a non-OK status, missing
    results, or a count mismatch, and ``NO_DATA`` when any point's elevation
    is null (outside dataset coverage).
    """
    status: Any = payload.get("status")
    if status != "OK":
        message: Any = payload.get("error", "no elevation data available")
        raise DemError("API_ERROR", str(message))
    results: Any = payload.get("results")
    if not isinstance(results, list):
        raise DemError("API_ERROR", "response missing results list")
    if len(results) != expected_count:
        raise DemError(
            "API_ERROR",
            f"expected {expected_count} results, got {len(results)}",
        )
    elevations: list[float] = []
    for i, result in enumerate(results):
        elevation: Any = result.get("elevation") if isinstance(result, dict) else None
        if elevation is None:
            raise DemError("NO_DATA", f"point {i} is outside EU-DEM dataset coverage")
        elevations.append(float(elevation))
    return elevations


def fetch_elevations(
    points: list[tuple[float, float]],
    transport: Transport | None = None,
) -> list[float]:
    """Fetch elevations (meters above sea level) for (lat, lng) points.

    Points are batched at :data:`MAX_POINTS_PER_REQUEST` per request and the
    returned list preserves input order. Raises :class:`DemError` on any
    failure (no partial results — a failed batch fails the call).
    """
    if not points:
        return []
    do_fetch: Transport = transport if transport is not None else _default_transport
    elevations: list[float] = []
    for start in range(0, len(points), MAX_POINTS_PER_REQUEST):
        chunk: list[tuple[float, float]] = points[
            start : start + MAX_POINTS_PER_REQUEST
        ]
        url: str = build_request_url(chunk)
        try:
            payload: dict[str, Any] = do_fetch(url)
        except DemError:
            raise
        except Exception as exc:  # noqa: BLE001 - structured network error
            raise DemError("NETWORK_ERROR", str(exc)) from exc
        elevations.extend(parse_response(payload, len(chunk)))
    return elevations

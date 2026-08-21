"""Pure coordinate logic: q,r,s parsing/validation and plane transforms.

This module is bpy-free so it can be unit-tested with normal Python
(design doc §14.2). It owns the strict q,r,s parser and the structured
``Issue`` type used across the add-on for validation reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import re

# Exactly an optional sign followed by base-10 digits. Rejects decimals,
# junk text, and Python int() quirks such as underscores ("1_0").
_INT_RE: re.Pattern[str] = re.compile(r"^[+-]?\d+$")

_SQRT3: float = math.sqrt(3.0)


class HexOrientation(Enum):
    """Hex orientation for the cube-to-plane mapping (design doc §7.2)."""

    POINTY = "POINTY"
    FLAT = "FLAT"


@dataclass(frozen=True)
class CubeCoord:
    """A hex cube coordinate (q, r, s) with the invariant q + r + s == 0."""

    q: int
    r: int
    s: int


@dataclass(frozen=True)
class Issue:
    """A structured validation issue (design doc §12).

    severity is "error" (blocks generation) or "warning" (advisory).
    code is a stable machine-readable identifier. line is the 1-based
    input line the issue refers to, when applicable.
    """

    severity: str
    code: str
    message: str
    line: int | None = None


def parse_cube_coords(text: str) -> tuple[list[CubeCoord], list[Issue]]:
    """Parse a newline-delimited q,r,s list into coordinates and issues.

    Contract (design doc §6.5): blank lines are ignored; each nonblank
    line must be exactly three signed integers with q + r + s == 0;
    duplicates are rejected. If ANY issue is found the whole batch is
    rejected and an empty coordinate list is returned (all-or-nothing).
    """
    issues: list[Issue] = []
    coords: list[CubeCoord] = []
    seen: dict[tuple[int, int, int], int] = {}

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line: str = raw_line.strip()
        if not line:
            continue

        fields: list[str] = line.split(",")
        if len(fields) != 3:
            issues.append(
                Issue(
                    "error",
                    "MALFORMED_LINE",
                    f"Line {line_no}: expected exactly 3 comma-separated "
                    f"integers, got {len(fields)} field(s)",
                    line_no,
                )
            )
            continue

        values: list[int] = []
        malformed: bool = False
        for field in fields:
            token: str = field.strip()
            if not _INT_RE.match(token):
                issues.append(
                    Issue(
                        "error",
                        "MALFORMED_LINE",
                        f"Line {line_no}: {token!r} is not a signed integer",
                        line_no,
                    )
                )
                malformed = True
                break
            values.append(int(token))
        if malformed:
            continue

        q, r, s = values
        if q + r + s != 0:
            issues.append(
                Issue(
                    "error",
                    "NONZERO_SUM",
                    f"Line {line_no}: q+r+s must be 0, got "
                    f"{q}+{r}+{s}={q + r + s}",
                    line_no,
                )
            )
            continue

        key: tuple[int, int, int] = (q, r, s)
        if key in seen:
            issues.append(
                Issue(
                    "error",
                    "DUPLICATE_COORD",
                    f"Line {line_no}: duplicate coordinate {q},{r},{s} "
                    f"(first seen on line {seen[key]})",
                    line_no,
                )
            )
            continue

        seen[key] = line_no
        coords.append(CubeCoord(q, r, s))

    if issues:
        return [], issues
    return coords, []


def cube_to_plane(
    coord: CubeCoord, orientation: HexOrientation, hex_radius: float
) -> tuple[float, float]:
    """Convert a cube coordinate to a 2D hex-center plane position.

    Uses q and r as axial coordinates (s is redundant, §7.1). The result
    is a logical map-plane position in model units, scaled by the hex
    radius R (center-to-corner). Formulas per design doc §7.2.
    """
    q: float = float(coord.q)
    r: float = float(coord.r)
    if orientation is HexOrientation.POINTY:
        x: float = hex_radius * _SQRT3 * (q + r / 2.0)
        y: float = hex_radius * 1.5 * r
    else:
        x = hex_radius * 1.5 * q
        y = hex_radius * _SQRT3 * (r + q / 2.0)
    return x, y

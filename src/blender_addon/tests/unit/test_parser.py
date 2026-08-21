"""Border tests for the q,r,s coordinate parser (design doc §6.5).

Asserts outcomes only: what coordinates come out, and what issues are
reported (with line numbers). No implementation details.
"""

from __future__ import annotations

from hex_heightmap_generator.coordinates import CubeCoord, parse_cube_coords


def test_accepts_signed_integers() -> None:
    coords, issues = parse_cube_coords("0,0,0\n1,-1,0\n-2,1,1")
    assert issues == []
    assert coords == [
        CubeCoord(0, 0, 0),
        CubeCoord(1, -1, 0),
        CubeCoord(-2, 1, 1),
    ]


def test_accepts_whitespace_around_commas() -> None:
    coords, issues = parse_cube_coords("  1 , -1 , 0  \n\t2,-2,0\t")
    assert issues == []
    assert coords == [CubeCoord(1, -1, 0), CubeCoord(2, -2, 0)]


def test_ignores_blank_lines() -> None:
    coords, issues = parse_cube_coords("\n0,0,0\n\n   \n1,-1,0\n")
    assert issues == []
    assert coords == [CubeCoord(0, 0, 0), CubeCoord(1, -1, 0)]


def test_empty_input_yields_no_coords_and_no_issues() -> None:
    coords, issues = parse_cube_coords("")
    assert coords == []
    assert issues == []


def test_rejects_missing_field() -> None:
    coords, issues = parse_cube_coords("1,0")
    assert coords == []
    assert len(issues) == 1
    assert issues[0].line == 1


def test_rejects_excess_field() -> None:
    coords, issues = parse_cube_coords("1,0,-1,0")
    assert coords == []
    assert len(issues) == 1
    assert issues[0].line == 1


def test_rejects_decimal() -> None:
    coords, issues = parse_cube_coords("1.0,0,-1")
    assert coords == []
    assert len(issues) == 1
    assert issues[0].line == 1


def test_rejects_junk_text() -> None:
    coords, issues = parse_cube_coords("abc,0,-1")
    assert coords == []
    assert len(issues) == 1
    assert issues[0].line == 1


def test_rejects_nonzero_sum() -> None:
    coords, issues = parse_cube_coords("1,1,1")
    assert coords == []
    assert len(issues) == 1
    assert issues[0].line == 1


def test_rejects_duplicate_coordinates_reporting_both_lines() -> None:
    coords, issues = parse_cube_coords("0,0,0\n1,-1,0\n0,0,0")
    assert coords == []
    assert len(issues) == 1
    assert issues[0].line == 3
    assert "1" in issues[0].message  # references the first occurrence's line


def test_issue_line_numbers_are_1_based() -> None:
    coords, issues = parse_cube_coords("\n\njunk,0,0")
    assert coords == []
    assert len(issues) == 1
    assert issues[0].line == 3

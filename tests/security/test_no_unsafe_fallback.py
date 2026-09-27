"""Non-skippable SEC-007 production-source guards."""

from __future__ import annotations

import pathlib
import re


REPO_ROOT = pathlib.Path(__file__).parents[2]
PRODUCTION_ROOT = REPO_ROOT / "assurance_system"
EXACT_UNSAFE_PATTERN = re.compile(r"weights_only\s*=\s*False")
BROAD_UNSAFE_PATTERN = re.compile(r"weights_only.*False")


def _production_python_files() -> list[pathlib.Path]:
    assert PRODUCTION_ROOT.is_dir(), "assurance_system production directory is missing"
    files = sorted(PRODUCTION_ROOT.rglob("*.py"))
    assert files, "SEC-007 scan would be vacuous: no production Python files found"
    return files


def _matches(pattern: re.Pattern[str]) -> list[str]:
    matches: list[str] = []
    for path in _production_python_files():
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if pattern.search(line):
                matches.append(f"{path.relative_to(REPO_ROOT)}:{line_number}")
    return matches


def test_sec_007_scan_is_nonvacuous() -> None:
    assert _production_python_files()


def test_sec_007_exact_unsafe_pattern_absent() -> None:
    assert _matches(EXACT_UNSAFE_PATTERN) == []


def test_sec_007_broad_unsafe_pattern_absent() -> None:
    assert _matches(BROAD_UNSAFE_PATTERN) == []

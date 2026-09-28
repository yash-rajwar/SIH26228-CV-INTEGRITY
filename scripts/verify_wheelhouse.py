"""Verify a pre-staged Python wheelhouse without using a package index.

This utility is validation tooling for TASK-027.  It does not establish an
offline-deployment claim by itself; that claim requires OFF-001 through
OFF-004 to pass on the approved target host.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


CORE_REQUIREMENTS = ("torch>=2.10.0", "onnx", "pycocotools")
IMPORT_NAMES = ("onnx", "torch", "pycocotools")


def _distribution_name(requirement: str) -> str:
    """Return a normalized distribution name from a simple wheel requirement."""

    candidate = requirement.split(";", 1)[0].strip()
    if not candidate or candidate.startswith("-"):
        raise ValueError(f"unsupported requirement entry: {requirement!r}")
    if "://" in candidate or " @ " in candidate:
        raise ValueError(
            f"URL/direct-reference requirement is not permitted: {requirement!r}"
        )

    end = len(candidate)
    for marker in ("[", "<", ">", "=", "!", "~", " "):
        position = candidate.find(marker)
        if position >= 0:
            end = min(end, position)
    name = candidate[:end].strip()
    if not name:
        raise ValueError(f"cannot determine distribution name: {requirement!r}")
    return name.lower().replace("-", "_").replace(".", "_")


def _project_requirements(requirements_path: Path) -> list[str]:
    """Read active requirement entries; comments and blank lines are ignored."""

    requirements: list[str] = []
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirement = line.split(" #", 1)[0].strip()
        if requirement:
            _distribution_name(requirement)
            requirements.append(requirement)
    return requirements


def _required_packages(requirements_path: Path) -> list[str]:
    """Merge mandatory packages with active project requirements by name."""

    merged: dict[str, str] = {
        _distribution_name(requirement): requirement
        for requirement in CORE_REQUIREMENTS
    }
    for requirement in _project_requirements(requirements_path):
        merged[_distribution_name(requirement)] = requirement
    return list(merged.values())


def _wheel_candidates(wheelhouse_dir: Path, distribution_name: str) -> list[Path]:
    """Return wheels whose normalized filename distribution matches the package."""

    candidates: list[Path] = []
    for wheel_path in sorted(wheelhouse_dir.glob("*.whl")):
        wheel_distribution = wheel_path.name.split("-", 1)[0]
        normalized = wheel_distribution.lower().replace("-", "_").replace(".", "_")
        if normalized == distribution_name:
            candidates.append(wheel_path)
    return candidates


def _offline_environment() -> dict[str, str]:
    """Return a pip environment with index and proxy configuration disabled."""

    environment = os.environ.copy()
    for variable in (
        "PIP_INDEX_URL",
        "PIP_EXTRA_INDEX_URL",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        environment.pop(variable, None)
    environment["PIP_CONFIG_FILE"] = os.devnull
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    environment["PIP_NO_INDEX"] = "1"
    return environment


def _pip_base_command(python: Path, wheelhouse_dir: Path) -> list[str]:
    return [
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-index",
        f"--find-links={wheelhouse_dir}",
        "--only-binary=:all:",
    ]


def _is_compatible(
    python: Path,
    wheelhouse_dir: Path,
    requirement: str,
    environment: dict[str, str],
) -> bool:
    """Ask the selected interpreter's pip to resolve one local wheel closure."""

    command = _pip_base_command(python, wheelhouse_dir) + [
        "--ignore-installed",
        "--dry-run",
        requirement,
    ]
    completed = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        shell=False,
        env=environment,
    )
    return completed.returncode == 0


def _install_locally(
    python: Path,
    wheelhouse_dir: Path,
    target_dir: Path,
    requirements: list[str],
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    command = _pip_base_command(python, wheelhouse_dir) + [
        "--target",
        str(target_dir),
        "--no-compile",
        *requirements,
    ]
    return subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        shell=False,
        env=environment,
    )


def _validate_import(
    python: Path,
    target_dir: Path,
    import_name: str,
    environment: dict[str, str],
) -> bool:
    target_literal = repr(str(target_dir.resolve()))
    import_literal = repr(import_name)
    code = (
        "import importlib, os, sys; "
        f"root=os.path.realpath({target_literal}); "
        "sys.path.insert(0, root); "
        f"module=importlib.import_module({import_literal}); "
        "origin=os.path.realpath(module.__file__); "
        "assert os.path.commonpath((root, origin)) == root"
    )
    completed = subprocess.run(
        [str(python), "-I", "-S", "-c", code],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        shell=False,
        env=environment,
    )
    return completed.returncode == 0


def _print_help() -> None:
    print(
        "usage: verify_wheelhouse.py [-h] "
        "[--wheelhouse-dir WHEELHOUSE_DIR] [--python PYTHON]\n\n"
        "Verify local wheel staging, compatibility, installation, and imports "
        "without accessing a package index.\n\n"
        "options:\n"
        "  -h, --help            show this help message and exit\n"
        "  --wheelhouse-dir WHEELHOUSE_DIR\n"
        "                        local wheelhouse directory (default: wheelhouse/)\n"
        "  --python PYTHON       Python interpreter used for pip and import checks\n"
        "                        (default: current)"
    )


def _parse_args(argv: list[str]) -> tuple[str, str] | None:
    wheelhouse_dir = "wheelhouse"
    python = sys.executable
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument in ("-h", "--help"):
            _print_help()
            return None
        if argument in ("--wheelhouse-dir", "--python"):
            if index + 1 >= len(argv):
                raise ValueError(f"missing value for {argument}")
            value = argv[index + 1]
            if argument == "--wheelhouse-dir":
                wheelhouse_dir = value
            else:
                python = value
            index += 2
            continue
        if argument.startswith("--wheelhouse-dir="):
            wheelhouse_dir = argument.split("=", 1)[1]
            index += 1
            continue
        if argument.startswith("--python="):
            python = argument.split("=", 1)[1]
            index += 1
            continue
        raise ValueError(f"unrecognized argument: {argument}")
    return wheelhouse_dir, python


def main(argv: list[str] | None = None) -> int:
    try:
        parsed = _parse_args(sys.argv[1:] if argv is None else argv)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        print("Run with --help for usage.", file=sys.stderr)
        return 1
    if parsed is None:
        return 0

    wheelhouse_argument, python_argument = parsed
    wheelhouse_dir = Path(wheelhouse_argument).resolve()
    python = Path(python_argument).resolve()
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"

    if not wheelhouse_dir.is_dir():
        print(f"ERROR: wheelhouse directory not found: {wheelhouse_dir}")
        return 1
    if not python.is_file():
        print(f"ERROR: Python interpreter not found: {python}")
        return 1
    if not requirements_path.is_file():
        print(f"ERROR: requirements file not found: {requirements_path}")
        return 1

    try:
        requirements = _required_packages(requirements_path)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: cannot read project requirements: {error}")
        return 1

    environment = _offline_environment()
    package_results: dict[str, bool] = {}

    print("PACKAGE STATUS")
    for requirement in requirements:
        distribution_name = _distribution_name(requirement)
        candidates = _wheel_candidates(wheelhouse_dir, distribution_name)
        cpu_wheel_present = distribution_name != "torch" or any(
            "+cpu" in candidate.name.lower() for candidate in candidates
        )
        compatible = bool(candidates) and cpu_wheel_present and _is_compatible(
            python,
            wheelhouse_dir,
            requirement,
            environment,
        )
        package_results[distribution_name] = compatible
        print(f"{requirement}: {'STAGED' if compatible else 'MISSING'}")

    with tempfile.TemporaryDirectory(prefix="assurance-wheelhouse-") as temp_dir:
        target_dir = Path(temp_dir) / "site-packages"
        target_dir.mkdir()
        install_result = _install_locally(
            python,
            wheelhouse_dir,
            target_dir,
            requirements,
            environment,
        )
        install_passed = install_result.returncode == 0
        print(f"INSTALL STATUS: {'PASS' if install_passed else 'FAIL'}")
        if not install_passed:
            diagnostic = (install_result.stderr or install_result.stdout).strip()
            if diagnostic:
                print(diagnostic)

        print("IMPORT STATUS")
        import_results: dict[str, bool] = {}
        for import_name in IMPORT_NAMES:
            import_passed = _validate_import(
                python,
                target_dir,
                import_name,
                environment,
            )
            import_results[import_name] = import_passed
            print(f"{import_name}: {'PASS' if import_passed else 'FAIL'}")

    all_staged = bool(package_results) and all(package_results.values())
    all_imported = all(import_results.values())
    return 0 if all_staged and install_passed and all_imported else 1


if __name__ == "__main__":
    raise SystemExit(main())

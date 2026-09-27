"""
cli.py — Top-level entry point for the SIH26228 CV Integrity Assurance System.
Delegates to assurance_system.interfaces.cli.

Authority: 10_TECHNICAL_SPECIFICATION_SIH26228.md §2.4
Implementation task: TASK-023

Entry points (to be implemented):
  assess         — python cli.py assess --submission <manifest_path>
  show-finding   — python cli.py show-finding --asset-id <id>
  show-evidence  — python cli.py show-evidence --asset-id <id> --method <method-id>
  show-audit-trail — python cli.py show-audit-trail
  export-bundle  — python cli.py export-bundle --asset-id <id> --output <path>
  list-deferred  — python cli.py list-deferred
  dashboard      — python cli.py dashboard --port <port>

STUB — not yet implemented.
"""

import sys


def main():
    print(
        "SIH26228 CV Integrity Assurance System — skeleton only.\n"
        "Implementation has not begun. See 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()

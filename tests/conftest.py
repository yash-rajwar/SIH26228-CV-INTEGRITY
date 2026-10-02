"""Test-only asset permissions for Windows restricted workers.

Python 3.13 mode-0700 pytest directories under built-in Administrator have
Administrators/OWNER_RIGHTS DACLs. Submitted test assets must be readable by the
restricted derivative. Grant READ/EXECUTE only, not write, on fresh test roots.
Production stores, repository assets and deployment ACLs are never changed here.
"""
import sys
import pytest


@pytest.fixture(autouse=True)
def readable_windows_test_assets(tmp_path):
    if sys.platform == "win32":
        from assurance_system.supervisor.windows_token import _API, current_token_state
        _API().grant_directory(tmp_path, current_token_state()["user_sid"], "GRGX")

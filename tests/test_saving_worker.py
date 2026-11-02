"""Exercise the real saving worker in fresh processes, isolating its global queue."""

import subprocess
import sys
from pathlib import Path

import pytest


def run_child(case):
    helper = Path(__file__).with_name("saving_worker_cases.py")
    result = subprocess.run(
        [sys.executable, "-B", str(helper), case],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_removed_queued_agent_does_not_stop_later_saves():
    run_child("removed_queued_agent")


def test_sync_error_reaches_caller_and_worker_continues():
    run_child("sync_error")


def test_successful_fallback_keeps_sync_saving_successful():
    run_child("successful_fallback")


def test_sync_all_agents_attempts_remaining_agents_before_raising():
    run_child("all_agents")


@pytest.mark.parametrize("reason", ["time", "level"])
def test_expected_skips_are_not_save_failures(reason):
    run_child(f"skip_{reason}")

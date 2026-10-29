"""Exercise the real saving worker in fresh processes, isolating its global queue."""

import subprocess
import sys
import textwrap

import pytest

SETUP = """
import queue
import threading
from configparser import ConfigParser
from types import SimpleNamespace

import alfred3.saving_agent as sa
from alfred3.exceptions import SavingAgentRunException

sa._quit_event.set()
sa._thread.join(3)
assert not sa._thread.is_alive()
sa._queue = queue.PriorityQueue()
sa._quit_event.clear()

config = ConfigParser()
config.read_dict({'general': {'debug': 'false'}, 'data': {'save_data': 'true'}})
exp = SimpleNamespace(config=config, exp_id='synthetic-worker',
    session_id='synthetic-session',
    movement_manager=SimpleNamespace(current_page=None, last_page=None))
saved = []

class Agent(sa.SavingAgent):
    def _save(self, data):
        if data.get('fail'):
            raise OSError('synthetic write failure')
        saved.append(dict(data))

controller = sa.SavingAgentController(exp)
good = Agent(experiment=exp, name='good', activation_level=1)
controller.append(good)

def start_worker():
    sa._thread = threading.Thread(target=sa._save_looper, args=(.01,), daemon=True)
    sa._thread.start()
"""


def run_child(body):
    result = subprocess.run(
        [sys.executable, "-B", "-c", SETUP + "\n" + textwrap.dedent(body)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_removed_queued_agent_does_not_stop_later_saves():
    run_child("""
        levels = []
        class Capture(sa.logging.Handler):
            def emit(self, record):
                levels.append(record.levelno)
        sa._logger.addHandler(Capture())
        removed = Agent(experiment=exp, name='removed', activation_level=1)
        controller.append(removed)
        controller.save_with_agent({}, 'removed', level=1)
        first_event = sa._queue.queue[0][4]
        controller.remove_agent('removed')
        start_worker()
        controller.save_with_agent({'value': 7}, 'good', level=1, sync=True)
        assert first_event.wait(1)
        assert isinstance(first_event.exception, KeyError)
        assert sa.logging.CRITICAL in levels
        assert saved == [{'value': 7}]
        assert sa._thread.is_alive()
        sa.wait_for_saving_thread()
        assert sa._queue.unfinished_tasks == 0
    """)


def test_sync_error_reaches_caller_and_worker_continues():
    run_child("""
        start_worker()
        try:
            controller.save_with_agent({}, 'missing', level=1, sync=True)
        except SavingAgentRunException as exc:
            assert isinstance(exc.__cause__, KeyError)
        else:
            raise AssertionError('Missing agent must fail the synchronous call')
        try:
            controller.save_with_agent({'fail': True}, 'good', level=1, sync=True)
        except SavingAgentRunException:
            pass
        else:
            raise AssertionError('An unsaved snapshot must be reported to the caller')
        controller.save_with_agent({'value': 9}, 'good', level=1, sync=True)
        assert saved == [{'value': 9}]
        assert sa._thread.is_alive()
        sa.wait_for_saving_thread()
    """)


def test_successful_fallback_keeps_sync_saving_successful():
    run_child("""
        class FailingAgent(Agent):
            def _save(self, data):
                raise OSError('synthetic primary failure')
        primary = FailingAgent(experiment=exp, name='primary', activation_level=1)
        primary.append_fallback(good)
        controller.append(primary)
        start_worker()
        controller.save_with_agent({'value': 11}, 'primary', level=1, sync=True)
        assert saved == [{'value': 11}]
        sa.wait_for_saving_thread()
    """)


def test_sync_all_agents_attempts_remaining_agents_before_raising():
    run_child("""
        class FailingAgent(Agent):
            def _save(self, data):
                raise OSError('synthetic primary failure')
        controller.remove_agent('good')
        controller.append(
            FailingAgent(experiment=exp, name='first', activation_level=1)
        )
        controller.append(good)
        start_worker()
        try:
            controller.save_with_all_agents({'value': 13}, level=1, sync=True)
        except SavingAgentRunException:
            pass
        else:
            raise AssertionError('An agent failure must reach the caller')
        assert saved == [{'value': 13}]
        assert sa._thread.is_alive()
        sa.wait_for_saving_thread()
    """)


@pytest.mark.parametrize("reason", ["time", "level"])
def test_expected_skips_are_not_save_failures(reason):
    run_child(f"""
        class SkippingAgent(Agent):
            def save_data(self, **kwargs):
                return False, {reason!r}
        controller.append(SkippingAgent(experiment=exp, name='skip'))
        start_worker()
        controller.save_with_agent({{}}, 'skip', level=1, sync=True)
        assert saved == []
        assert sa._thread.is_alive()
        sa.wait_for_saving_thread()
    """)

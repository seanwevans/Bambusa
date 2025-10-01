import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

from bambusa.debug.timeline import Timeline
from bambusa.runtime.executor import Executor
from bambusa.runtime.persistent_heap import PersistentHeap


@pytest.fixture()
def sample_log(tmp_path: Path) -> Path:
    steps = [
        {"op": "assign", "target": "x", "value": 1},
        {"op": "add", "target": "x", "value": 2},
        {"op": "mask_select", "target": "y", "mask": True, "on_true": 3, "on_false": 0},
        {"op": "emit", "channel": "stdout", "value": "done"},
    ]
    executor = Executor(steps, initial_state={"x": 0})
    log_path = tmp_path / "run.log"
    executor.run(log_path=log_path)
    return log_path


@pytest.fixture()
def persistent_vector_log(tmp_path: Path) -> Path:
    heap = PersistentHeap()
    vector = heap.allocate([1, 2, 3])
    nested = {
        "vector": vector,
        "items": [vector, {"inner": vector}],
    }
    initial_state = {
        "vec": vector,
        "nested": nested,
        "emissions": {},
    }
    steps = [
        {"op": "add", "target": "counter", "value": 1},
        {"op": "mul", "target": "counter", "value": 2},
    ]
    executor = Executor(steps, initial_state=initial_state)
    log_path = tmp_path / "persistent_vector.log"
    executor.run(log_path=log_path)
    return log_path


def test_timeline_navigation(sample_log: Path) -> None:
    timeline = Timeline.from_log(sample_log)

    assert timeline.current_step == 0
    assert timeline.current_state["x"] == 1

    timeline.next()
    assert timeline.current_step == 1
    assert timeline.current_state["x"] == 3

    timeline.seek(0)
    with pytest.raises(IndexError):
        timeline.prev()

    timeline.seek(3)
    assert timeline.current_state["emissions"]["stdout"] == ["done"]
    with pytest.raises(IndexError):
        timeline.next()


def test_timeline_fork_and_diff(sample_log: Path) -> None:
    root = Timeline.from_log(sample_log)
    fork = root.fork(at_step=1)

    diff = fork.diff(root, step=1, other_step=2)
    assert diff["added"].get("y") == 3
    assert "x" not in diff["changed"]

    # Move fork forward and ensure states diverge
    fork.next()
    fork_state = fork.current_state
    root.seek(3)
    delta = fork.diff(root, other_step=root.current_step)
    assert delta["changed"]["emissions"]["right"] == root.current_state["emissions"]
    assert delta["changed"]["emissions"]["left"] == fork_state["emissions"]


def test_timeline_diff_defaults_to_other_current_step(sample_log: Path) -> None:
    root = Timeline.from_log(sample_log)
    fork = root.fork()

    fork.seek(2)
    root.seek(0)

    diff = fork.diff(root, step=2)

    assert diff["removed"].get("y") == 3
    assert diff["changed"]["x"]["left"] == 3
    assert diff["changed"]["x"]["right"] == 1


def test_cli_json_mode(sample_log: Path) -> None:
    log = sample_log
    env = os.environ.copy()
    src_path = str(Path.cwd() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src_path, existing]) if existing else src_path
    result = subprocess.run(
        [sys.executable, "-m", "bambusa", "timeline", str(log), "--json"],
        check=True,
        capture_output=True,
        env=env,
    )
    payload = json.loads(result.stdout.decode("utf-8"))
    assert len(payload) == 4
    assert payload[0]["state"]["x"] == 1


def test_cli_json_mode_with_persistent_vector(persistent_vector_log: Path) -> None:
    env = os.environ.copy()
    src_path = str(Path.cwd() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src_path, existing]) if existing else src_path
    result = subprocess.run(
        [sys.executable, "-m", "bambusa", "timeline", str(persistent_vector_log), "--json"],
        check=True,
        capture_output=True,
        env=env,
    )
    payload = json.loads(result.stdout.decode("utf-8"))
    assert len(payload) == 2
    assert payload[0]["state"]["vec"] == [1, 2, 3]
    assert payload[1]["state"]["nested"]["vector"] == [1, 2, 3]
    assert payload[1]["state"]["nested"]["items"][1]["inner"] == [1, 2, 3]


def test_timeline_from_stream(sample_log: Path) -> None:
    log_text = sample_log.read_text(encoding="utf-8")
    timeline = Timeline.from_stream(StringIO(log_text))

    assert timeline.size == 4
    assert timeline.current_step == 0
    timeline.seek(3)
    assert timeline.current_state["emissions"]["stdout"] == ["done"]


def test_cli_json_mode_stdin(sample_log: Path) -> None:
    env = os.environ.copy()
    src_path = str(Path.cwd() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src_path, existing]) if existing else src_path

    log_text = sample_log.read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "bambusa", "timeline", "-", "--json"],
        input=log_text,
        text=True,
        check=True,
        capture_output=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert len(payload) == 4
    assert payload[-1]["step"] == 3


def test_cli_json_mode_stdin_with_persistent_vector(persistent_vector_log: Path) -> None:
    env = os.environ.copy()
    src_path = str(Path.cwd() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src_path, existing]) if existing else src_path

    log_text = persistent_vector_log.read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "bambusa", "timeline", "-", "--json"],
        input=log_text,
        text=True,
        check=True,
        capture_output=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload[0]["state"]["vec"] == [1, 2, 3]
    assert payload[-1]["state"]["nested"]["items"][0] == [1, 2, 3]

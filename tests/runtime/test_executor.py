import json
from pathlib import Path

import pytest

from bambusa.runtime.executor import Executor, StructuredLogWriter


def test_mul_initialises_missing_register_to_operand() -> None:
    executor = Executor([
        {
            "op": "mul",
            "target": "result",
            "value": 7,
        }
    ])

    executor.run()

    assert executor.state["result"] == 7


def test_structured_log_writer_rejects_non_positive_flush_interval(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        StructuredLogWriter(tmp_path / "run.log", flush_interval=0)


def test_executor_log_remains_complete_and_valid_with_buffered_writer(tmp_path: Path) -> None:
    steps = [
        {"op": "assign", "target": "counter", "value": 0},
        *({"op": "add", "target": "counter", "value": 1} for _ in range(500)),
        {"op": "emit", "channel": "stdout", "value": "done"},
    ]
    executor = Executor(steps)
    log_path = tmp_path / "buffered-run.log"

    snapshots = executor.run(log_path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(steps)
    parsed = [json.loads(line) for line in lines]
    assert [entry["step"] for entry in parsed] == list(range(len(steps)))
    assert parsed[-1]["state"]["emissions"]["stdout"] == ["done"]
    assert parsed == snapshots

"""Runtime executor for Bambusa IR with structured logging.

This module provides a small, test-focused executor for Bambusa's toy
intermediate representation.  The executor understands a handful of
high-level operations that are sufficient for the unit tests and emits a
structured log containing a snapshot of the runtime state after every step.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional
import json
import copy


@dataclass
class IRStep:
    """Represents a single Bambusa IR step.

    Parameters
    ----------
    op:
        The opcode to execute.  Supported opcodes are ``assign``, ``add``,
        ``mul``, ``mask_select`` and ``emit``.
    args:
        Arguments for the opcode.  The expected shape depends on the opcode:

        ``assign``
            ``{"target": str, "value": Any}``
        ``add``
            ``{"target": str, "value": Any}`` – the value is added to the
            current value of the target variable (defaulting to ``0``).
        ``mul``
            ``{"target": str, "value": Any}`` – multiplies the current value
            by the provided value.
        ``mask_select``
            ``{"target": str, "mask": bool, "on_true": Any, "on_false": Any}``
            – stores ``on_true`` when the mask is truthy, otherwise ``on_false``.
        ``emit``
            ``{"channel": str, "value": Any}`` – appends the value to the
            ``emissions`` buffer under the given channel.
    """

    op: str
    args: Mapping[str, Any]


class StructuredLogWriter:
    """Writes structured JSON snapshots for the executor."""

    def __init__(self, destination: Path | str | None):
        self._path: Optional[Path] = None
        self._file = None
        if destination is not None:
            self._path = Path(destination)
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self._path.open("w", encoding="utf-8")

    def snapshot(self, *, step: int, instruction: Mapping[str, Any], state: Mapping[str, Any]) -> None:
        """Write a snapshot entry.

        Parameters
        ----------
        step:
            The zero-based step index.
        instruction:
            A JSON-serialisable representation of the IR step that just
            executed.
        state:
            A mapping describing the current runtime state.  The mapping is
            copied before serialisation to ensure immutability of historical
            entries.
        """

        if self._file is None:
            return
        entry = {
            "step": step,
            "instruction": instruction,
            "state": copy.deepcopy(state),
        }
        json.dump(entry, self._file, sort_keys=True)
        self._file.write("\n")
        self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def __enter__(self) -> "StructuredLogWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class Executor:
    """Executes Bambusa IR steps and records a timeline of states."""

    def __init__(
        self,
        steps: Iterable[IRStep | Mapping[str, Any]],
        *,
        initial_state: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._steps: List[IRStep] = [self._normalise(step) for step in steps]
        self.state: Dict[str, Any] = dict(initial_state or {})
        self.state.setdefault("emissions", {})

    @staticmethod
    def _normalise(step: IRStep | Mapping[str, Any]) -> IRStep:
        if isinstance(step, IRStep):
            return step
        if "op" not in step:
            raise ValueError(f"Invalid IR step missing 'op': {step!r}")
        args = dict(step)
        op = args.pop("op")
        return IRStep(op=op, args=args)

    def run(self, *, log_path: Path | str | None = None) -> List[Dict[str, Any]]:
        """Execute all steps and optionally persist a structured log.

        Parameters
        ----------
        log_path:
            Optional path to a log file that will receive JSON-line snapshots
            after each executed step.

        Returns
        -------
        list of dict
            The full list of snapshot entries generated during execution.  The
            same payload is written to ``log_path`` when provided.
        """

        snapshots: List[Dict[str, Any]] = []
        with StructuredLogWriter(log_path) as writer:
            for index, step in enumerate(self._steps):
                self._execute_step(step)
                snapshot = {
                    "step": index,
                    "instruction": {"op": step.op, **step.args},
                    "state": copy.deepcopy(self.state),
                }
                writer.snapshot(
                    step=index,
                    instruction=snapshot["instruction"],
                    state=snapshot["state"],
                )
                snapshots.append(snapshot)
        return snapshots

    # ------------------------------------------------------------------
    # Internal helpers

    def _execute_step(self, step: IRStep) -> None:
        op = step.op
        handler_name = f"_handle_{op}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            raise ValueError(f"Unsupported IR operation: {op}")
        handler(step.args)

    def _handle_assign(self, args: Mapping[str, Any]) -> None:
        target = self._require(args, "target")
        value = args.get("value")
        self.state[target] = value

    def _handle_add(self, args: Mapping[str, Any]) -> None:
        target = self._require(args, "target")
        value = args.get("value", 0)
        self.state[target] = self.state.get(target, 0) + value

    def _handle_mul(self, args: Mapping[str, Any]) -> None:
        target = self._require(args, "target")
        value = args.get("value", 1)
        self.state[target] = self.state.get(target, 0) * value

    def _handle_mask_select(self, args: Mapping[str, Any]) -> None:
        target = self._require(args, "target")
        mask = bool(args.get("mask"))
        on_true = args.get("on_true")
        on_false = args.get("on_false")
        self.state[target] = on_true if mask else on_false

    def _handle_emit(self, args: Mapping[str, Any]) -> None:
        channel = self._require(args, "channel")
        value = args.get("value")
        emissions: MutableMapping[str, List[Any]] = self.state.setdefault("emissions", {})
        emissions.setdefault(channel, []).append(value)

    @staticmethod
    def _require(args: Mapping[str, Any], key: str) -> Any:
        if key not in args:
            raise ValueError(f"Missing required argument '{key}' for operation")
        return args[key]


__all__ = ["Executor", "IRStep", "StructuredLogWriter"]

"""Branchless IR execution harness built on the persistent heap."""
"""Runtime executor for Bambusa IR with structured logging.

This module provides a small, test-focused executor for Bambusa's toy
intermediate representation.  The executor understands a handful of
high-level operations that are sufficient for the unit tests and emits a
structured log containing a snapshot of the runtime state after every step.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, MutableMapping, Sequence

from .persistent_heap import PersistentHeap, PersistentVector, compact, masked_load, masked_store


from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional
import json
import copy

class Executor:
    """A tiny interpreter for the branchless Bambusa IR.

    The interpreter operates on a dictionary based IR where every instruction is
    represented as a mapping with an ``op`` key. Instructions may provide a
    ``target`` name to store the result. All operands can be either literals or
    names of previously computed values. Collections (lists/tuples) are resolved
    recursively, making it convenient to build programs using Python literals.
    """

    def __init__(self, heap: PersistentHeap | None = None) -> None:
        self.heap = heap or PersistentHeap()
        self.registers: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, program: Iterable[MutableMapping[str, Any]]) -> Dict[str, Any]:
        """Execute a program and return the resulting register map."""

        for instruction in program:
            op = instruction.get("op")
            if op is None:
                raise ValueError("Instruction missing 'op' field")
            handler = getattr(self, f"_op_{op}", None)
            if handler is None:
                raise ValueError(f"Unsupported operation: {op}")
            result = handler(instruction)
            target = instruction.get("target")
            if target is not None:
                self.registers[target] = result
        return self.registers

    # ------------------------------------------------------------------
    # Instruction helpers
    # ------------------------------------------------------------------
    def _resolve(self, operand: Any) -> Any:
        if isinstance(operand, str) and operand in self.registers:
            return self.registers[operand]
        if isinstance(operand, list):
            return [self._resolve(item) for item in operand]
        if isinstance(operand, tuple):
            return tuple(self._resolve(item) for item in operand)
        return operand

    # ------------------------------------------------------------------
    # Instruction implementations
    # ------------------------------------------------------------------
    def _op_const(self, instruction: MutableMapping[str, Any]) -> Any:
        return instruction.get("value")

    def _op_move(self, instruction: MutableMapping[str, Any]) -> Any:
        return self._resolve(instruction.get("value"))

    def _op_add(self, instruction: MutableMapping[str, Any]) -> Any:
        lhs = self._resolve(instruction.get("lhs"))
        rhs = self._resolve(instruction.get("rhs"))
        return lhs + rhs

    def _op_sub(self, instruction: MutableMapping[str, Any]) -> Any:
        lhs = self._resolve(instruction.get("lhs"))
        rhs = self._resolve(instruction.get("rhs"))
        return lhs - rhs

    def _op_mul(self, instruction: MutableMapping[str, Any]) -> Any:
        lhs = self._resolve(instruction.get("lhs"))
        rhs = self._resolve(instruction.get("rhs"))
        return lhs * rhs

    def _op_select(self, instruction: MutableMapping[str, Any]) -> Any:
        mask = self._resolve(instruction.get("mask"))
        true_value = self._resolve(instruction.get("true"))
        false_value = self._resolve(instruction.get("false"))
        return true_value if mask else false_value

    def _op_tuple(self, instruction: MutableMapping[str, Any]) -> Any:
        values = instruction.get("values", [])
        return tuple(self._resolve(v) for v in values)

    def _op_alloc(self, instruction: MutableMapping[str, Any]) -> PersistentVector:
        values = self._resolve(instruction.get("values", []))
        mask = None
        if "mask" in instruction:
            mask = self._resolve(instruction.get("mask"))
        fill_value = instruction.get("fill_value", 0)
        return self.heap.allocate(values, mask=mask, fill_value=fill_value)

    def _op_masked_load(self, instruction: MutableMapping[str, Any]) -> Any:
        vector = self._resolve(instruction.get("vector"))
        indices = self._resolve(instruction.get("indices"))
        mask = self._resolve(instruction.get("mask"))
        default = self._resolve(instruction.get("default")) if "default" in instruction else None
        return masked_load(vector, indices, mask, default)

    def _op_masked_store(self, instruction: MutableMapping[str, Any]) -> PersistentVector:
        vector = self._resolve(instruction.get("vector"))
        indices = self._resolve(instruction.get("indices"))
        values = self._resolve(instruction.get("values"))
        mask = self._resolve(instruction.get("mask"))
        return masked_store(vector, indices, values, mask)

    def _op_compact(self, instruction: MutableMapping[str, Any]) -> PersistentVector:
        vector = self._resolve(instruction.get("vector"))
        mask = self._resolve(instruction.get("mask"))
        return compact(vector, mask)

    def _op_len(self, instruction: MutableMapping[str, Any]) -> int:
        vector = self._resolve(instruction.get("vector"))
        return len(vector)

    def _op_index(self, instruction: MutableMapping[str, Any]) -> Any:
        vector = self._resolve(instruction.get("vector"))
        index = self._resolve(instruction.get("index"))
        if not isinstance(vector, PersistentVector):
            raise TypeError("index op expects a PersistentVector")
        return vector[index]

    # Utilities ---------------------------------------------------------
    def snapshot(self, names: Sequence[str]) -> Dict[str, Any]:
        """Return a snapshot of selected registers (materialising vectors)."""

        result: Dict[str, Any] = {}
        for name in names:
            value = self.registers.get(name)
            if isinstance(value, PersistentVector):
                result[name] = value.materialise()
            else:
                result[name] = value
        return result


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


"""Runtime executors for Bambusa IR.

The branchless executor operates on dictionary based instructions.  Opcodes
follow a simple naming scheme so they can be emitted mechanically from the
lowering pipeline:

* Arithmetic operations use short English verbs (``add``, ``sub``, ``mul``)
  that mirror :class:`bambusa.ir.Binary` nodes.
* Comparisons use the ``cmp_<mnemonic>`` form where ``<mnemonic>`` is the
  familiar LLVM-style suffix derived from the Bambusa surface syntax
  (``==`` → ``eq``, ``!=`` → ``ne``, ``<`` → ``lt``, ``<=`` → ``le``, ``>`` →
  ``gt``, ``>=`` → ``ge``).  This keeps the opcode names stable relative to
  :class:`bambusa.ir.Compare` operations while staying friendly to downstream
  interpreters.
"""
from __future__ import annotations

import json
import operator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from .persistent_heap import (
    PersistentHeap,
    PersistentVector,
    compact,
    masked_load,
    masked_store,
)


def _materialise_value(value: Any) -> Any:
    """Recursively materialise persistent vectors within ``value``."""

    if isinstance(value, PersistentVector):
        return value.materialise()
    if isinstance(value, Mapping):
        return {key: _materialise_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_materialise_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_materialise_value(item) for item in value)
    return value


def _materialise_state(state: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a copy of ``state`` with vectors materialised into tuples."""

    return {key: _materialise_value(value) for key, value in state.items()}


class BranchlessExecutor:
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
        if isinstance(operand, Mapping):
            if set(operand.keys()) == {"ref"}:
                return self.registers[operand["ref"]]
            return {key: self._resolve(value) for key, value in operand.items()}
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

    # Comparisons -----------------------------------------------------
    def _compare(self, instruction: MutableMapping[str, Any], op) -> bool:
        try:
            lhs_operand = instruction["lhs"]
            rhs_operand = instruction["rhs"]
        except KeyError as exc:  # pragma: no cover - sanity guard
            raise ValueError("comparison operations require 'lhs' and 'rhs'") from exc
        lhs = self._resolve(lhs_operand)
        rhs = self._resolve(rhs_operand)
        return op(lhs, rhs)

    def _op_cmp_eq(self, instruction: MutableMapping[str, Any]) -> bool:
        return self._compare(instruction, operator.eq)

    def _op_cmp_ne(self, instruction: MutableMapping[str, Any]) -> bool:
        return self._compare(instruction, operator.ne)

    def _op_cmp_lt(self, instruction: MutableMapping[str, Any]) -> bool:
        return self._compare(instruction, operator.lt)

    def _op_cmp_le(self, instruction: MutableMapping[str, Any]) -> bool:
        return self._compare(instruction, operator.le)

    def _op_cmp_gt(self, instruction: MutableMapping[str, Any]) -> bool:
        return self._compare(instruction, operator.gt)

    def _op_cmp_ge(self, instruction: MutableMapping[str, Any]) -> bool:
        return self._compare(instruction, operator.ge)

    def _op_select(self, instruction: MutableMapping[str, Any]) -> Any:
        mask = self._resolve(instruction.get("mask"))
        true_value = self._resolve(instruction.get("true"))
        false_value = self._resolve(instruction.get("false"))

        def _as_sequence(value: Any) -> Optional[Sequence[Any]]:
            if isinstance(value, PersistentVector):
                return value.materialise()
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                return value
            return None

        mask_seq = _as_sequence(mask)
        true_seq = _as_sequence(true_value)
        false_seq = _as_sequence(false_value)

        candidate_lengths = [
            len(seq)
            for seq in (mask_seq, true_seq, false_seq)
            if seq is not None
        ]
        target_length = max(candidate_lengths, default=None)

        # Treat fully scalar inputs (possibly length-1 sequences) as scalars.
        if target_length is None or (
            target_length == 1
            and (mask_seq is None or len(mask_seq) == 1)
            and (true_seq is None or len(true_seq) == 1)
            and (false_seq is None or len(false_seq) == 1)
        ):
            mask_value = bool(mask_seq[0]) if mask_seq is not None else bool(mask)
            true_scalar = true_seq[0] if true_seq is not None else true_value
            false_scalar = false_seq[0] if false_seq is not None else false_value
            return true_scalar if mask_value else false_scalar

        target_length = target_length or 0

        def _broadcast(seq: Optional[Sequence[Any]], value: Any) -> Sequence[Any]:
            if seq is None:
                return tuple(value for _ in range(target_length))
            if len(seq) == target_length:
                return tuple(seq)
            if len(seq) == 1:
                return tuple(seq[0] for _ in range(target_length))
            raise ValueError(
                f"Value of length {len(seq)} cannot broadcast to length {target_length}"
            )

        if mask_seq is None:
            mask_tuple = tuple(bool(mask) for _ in range(target_length))
        else:
            mask_tuple = tuple(bool(m) for m in _broadcast(mask_seq, mask))

        true_tuple = _broadcast(true_seq, true_value)
        false_tuple = _broadcast(false_seq, false_value)

        return tuple(
            true_item if mask_item else false_item
            for mask_item, true_item, false_item in zip(mask_tuple, true_tuple, false_tuple)
        )

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

        result: Dict[str, Any] = {name: self.registers.get(name) for name in names}
        return _materialise_state(result)


@dataclass
class IRStep:
    """Represents a single Bambusa IR step."""

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
        """Write a snapshot entry."""

        if self._file is None:
            return
        entry = {
            "step": step,
            "instruction": _materialise_state(instruction),
            "state": _materialise_state(state),
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

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401 - delegated cleanup
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
        """Execute all steps and optionally persist a structured log."""

        snapshots: List[Dict[str, Any]] = []
        with StructuredLogWriter(log_path) as writer:
            for index, step in enumerate(self._steps):
                self._execute_step(step)
                instruction = _materialise_state({"op": step.op, **step.args})
                state_snapshot = _materialise_state(self.state)
                snapshot = {
                    "step": index,
                    "instruction": instruction,
                    "state": state_snapshot,
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
        self.state[target] = self.state.get(target, 1) * value

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


__all__ = ["BranchlessExecutor", "Executor", "IRStep", "StructuredLogWriter"]

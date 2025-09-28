"""Branchless IR execution harness built on the persistent heap."""
from __future__ import annotations

from typing import Any, Dict, Iterable, MutableMapping, Sequence

from .persistent_heap import PersistentHeap, PersistentVector, compact, masked_load, masked_store


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


__all__ = ["Executor"]

"""Branchless Static Single Assignment (SSA) IR primitives for Bambusa."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass(slots=True, frozen=True)
class SSAValue:
    """An SSA value produced by an IR operation."""

    name: str
    type: str = "scalar"


@dataclass(slots=True, frozen=True)
class Mask(SSAValue):
    """Boolean mask value used to predicate side effects."""

    type: str = "mask"


@dataclass(slots=True, frozen=True)
class LoopIndex(SSAValue):
    """Logical induction variable for masked loops."""

    type: str = "index"


@dataclass(slots=True)
class Operation:
    """Base class for all IR operations."""

    output: Optional[SSAValue]


@dataclass(slots=True)
class Constant(Operation):
    value: object


@dataclass(slots=True)
class Unary(Operation):
    op: str
    operand: SSAValue


@dataclass(slots=True)
class Binary(Operation):
    op: str
    left: SSAValue
    right: SSAValue


@dataclass(slots=True)
class Compare(Operation):
    op: str
    left: SSAValue
    right: SSAValue


@dataclass(slots=True)
class Select(Operation):
    mask: Mask
    on_true: SSAValue
    on_false: SSAValue


@dataclass(slots=True)
class MaskedLoad(Operation):
    mask: Mask
    array: SSAValue
    index: SSAValue
    default: SSAValue


@dataclass(slots=True)
class MaskedStore(Operation):
    mask: Mask
    array: SSAValue
    index: SSAValue
    value: SSAValue


@dataclass(slots=True)
class MaskedLoop(Operation):
    """A loop lowered to a masked fold representation."""

    index: LoopIndex
    start: SSAValue
    end: SSAValue
    mask: Mask
    body: List[Operation] = field(default_factory=list)
    outputs: Dict[str, SSAValue] = field(default_factory=dict)


@dataclass(slots=True)
class IRFunction:
    name: str
    params: Dict[str, SSAValue]
    body: List[Operation]
    return_value: Optional[SSAValue] = None


@dataclass(slots=True)
class IRProgram:
    functions: List[IRFunction]


__all__ = [
    "Binary",
    "Compare",
    "Constant",
    "IRFunction",
    "IRProgram",
    "LoopIndex",
    "Mask",
    "MaskedLoad",
    "MaskedLoop",
    "MaskedStore",
    "Unary",
    "Operation",
    "SSAValue",
    "Select",
]


"""Lightweight AST nodes used by the lowering pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Tuple


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Expression:
    """Base class for expression nodes."""


@dataclass(frozen=True)
class Literal(Expression):
    value: object


@dataclass(frozen=True)
class Var(Expression):
    name: str


@dataclass(frozen=True)
class BinaryOp(Expression):
    left: Expression
    op: str
    right: Expression


@dataclass(frozen=True)
class Compare(Expression):
    left: Expression
    op: str
    right: Expression


@dataclass(frozen=True)
class Load(Expression):
    array: str
    index: Expression


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Statement:
    """Base class for statement nodes."""


@dataclass(frozen=True)
class Assign(Statement):
    target: str
    value: Expression


@dataclass(frozen=True)
class Store(Statement):
    array: str
    index: Expression
    value: Expression


@dataclass(frozen=True)
class IfElse(Statement):
    condition: Expression
    then_body: Sequence[Statement]
    else_body: Sequence[Statement] = field(default_factory=tuple)


@dataclass(frozen=True)
class ForLoop(Statement):
    target: str
    start: Expression
    end: Expression
    body: Sequence[Statement]


@dataclass(frozen=True)
class Return(Statement):
    value: Expression


# ---------------------------------------------------------------------------
# Program container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Function:
    name: str
    params: Sequence[str]
    body: Sequence[Statement]


@dataclass(frozen=True)
class Program:
    functions: Sequence[Function]


__all__ = [
    "Assign",
    "BinaryOp",
    "Compare",
    "Expression",
    "ForLoop",
    "Function",
    "IfElse",
    "Literal",
    "Load",
    "Program",
    "Return",
    "Statement",
    "Store",
    "Var",
]

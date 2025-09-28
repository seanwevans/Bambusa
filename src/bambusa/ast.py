"""Abstract syntax tree nodes for the Bambusa surface language prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence


class Expression:
    """Base class for expressions."""


class Statement:
    """Base class for statements."""


@dataclass(slots=True)
class Program:
    """A complete Bambusa program consisting of top-level functions."""

    functions: Sequence["Function"]


@dataclass(slots=True)
class Function:
    """A function declaration with a name, parameters, and body."""

    name: str
    params: Sequence[str]
    body: Sequence[Statement]


@dataclass(slots=True)
class Literal(Expression):
    value: object


@dataclass(slots=True)
class Var(Expression):
    name: str


@dataclass(slots=True)
class BinaryOp(Expression):
    left: Expression
    op: str
    right: Expression


@dataclass(slots=True)
class Compare(Expression):
    left: Expression
    op: str
    right: Expression


@dataclass(slots=True)
class Load(Expression):
    array: str
    index: Expression


@dataclass(slots=True)
class Assign(Statement):
    target: str
    value: Expression


@dataclass(slots=True)
class Store(Statement):
    array: str
    index: Expression
    value: Expression


@dataclass(slots=True)
class IfElse(Statement):
    condition: Expression
    then_body: Sequence[Statement] = field(default_factory=list)
    else_body: Sequence[Statement] = field(default_factory=list)


@dataclass(slots=True)
class ForLoop(Statement):
    target: str
    start: Expression
    end: Expression
    body: Sequence[Statement]


@dataclass(slots=True)
class Return(Statement):
    value: Expression


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

"""Typed abstract syntax tree definitions for the Bambusa language."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class SourceLocation:
    """Represents a point in the original source program."""

    line: int
    column: int


@dataclass(frozen=True)
class Type:
    """Base class for Bambusa types."""

    def is_numeric(self) -> bool:
        return False

    def is_bool(self) -> bool:
        return False

    def __str__(self) -> str:  # pragma: no cover - presentation helper
        return self.__class__.__name__


@dataclass(frozen=True)
class PrimitiveType(Type):
    """Represents primitive scalar types."""

    name: str

    def is_numeric(self) -> bool:
        return self.name in {"int", "float"}

    def is_bool(self) -> bool:
        return self.name == "bool"

    def __str__(self) -> str:  # pragma: no cover - presentation helper
        return self.name


@dataclass(frozen=True)
class ArrayType(Type):
    """An array type with a homogeneous element type."""

    element_type: Type

    def __str__(self) -> str:  # pragma: no cover - presentation helper
        return f"{self.element_type}[]"


INT_TYPE = PrimitiveType("int")
FLOAT_TYPE = PrimitiveType("float")
BOOL_TYPE = PrimitiveType("bool")
VOID_TYPE = PrimitiveType("void")


@dataclass
class Node:
    """Base class for all AST nodes."""

    location: SourceLocation


@dataclass
class Statement(Node):
    """Base class for statements."""


@dataclass
class Expression(Node):
    """Base class for expressions."""

    inferred_type: Optional[Type] = field(init=False, default=None)


@dataclass
class Literal(Expression):
    value: object


@dataclass
class Identifier(Expression):
    name: str


@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression


@dataclass
class BinaryOp(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass
class ConditionalExpr(Expression):
    condition: Expression
    then_expr: Expression
    else_expr: Expression


@dataclass
class Block(Statement):
    statements: List[Statement]


@dataclass
class ExprStmt(Statement):
    value: Expression


@dataclass
class VarDecl(Statement):
    type: Type
    name: str
    initializer: Optional[Expression] = None


@dataclass
class Assignment(Statement):
    name: str
    value: Expression

    @property
    def target(self) -> str:
        return self.name


@dataclass
class IfStmt(Statement):
    condition: Expression
    then_block: Block
    else_block: Optional[Block] = None


@dataclass
class Range(Node):
    start: Expression
    end: Expression


@dataclass
class ForStmt(Statement):
    iterator: str
    range: Range
    body: Block


@dataclass
class ReturnStmt(Statement):
    value: Expression


@dataclass
class Parameter(Node):
    type: Type
    name: str


@dataclass
class FunctionDecl(Node):
    name: str
    params: List[Parameter]
    return_type: Type
    body: Block


@dataclass
class GlobalDecl(Node):
    type: Type
    name: str
    value: Expression


@dataclass
class Program(Node):
    globals: List[GlobalDecl]
    functions: List[FunctionDecl]


__all__ = [
    "ArrayType",
    "Assignment",
    "BinaryOp",
    "Block",
    "BOOL_TYPE",
    "ConditionalExpr",
    "ExprStmt",
    "FLOAT_TYPE",
    "ForStmt",
    "FunctionDecl",
    "GlobalDecl",
    "INT_TYPE",
    "Identifier",
    "IfStmt",
    "Literal",
    "Parameter",
    "Program",
    "Range",
    "ReturnStmt",
    "SourceLocation",
    "Statement",
    "Type",
    "UnaryOp",
    "VarDecl",
    "VOID_TYPE",
]

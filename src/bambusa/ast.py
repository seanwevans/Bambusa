"""Abstract syntax tree definitions for the Bambusa language."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union


# ---------------------------------------------------------------------------
# Source locations
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceLocation:
    """Represents the location of a node in the original source."""

    line: int
    column: int


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class Type:
    """Base class for Bambusa types."""

    def __str__(self) -> str:  # pragma: no cover - helper for diagnostics
        raise NotImplementedError

    def is_numeric(self) -> bool:
        return False

    def is_bool(self) -> bool:
        return False


@dataclass(frozen=True)
class PrimitiveType(Type):
    """Primitive scalar types."""

    name: str

    def __post_init__(self) -> None:
        if self.name not in {"int", "float", "bool", "void"}:
            raise ValueError(f"unknown primitive type '{self.name}'")

    def __str__(self) -> str:  # pragma: no cover - helper for diagnostics
        return self.name

    def is_numeric(self) -> bool:
        return self.name in {"int", "float"}

    def is_bool(self) -> bool:
        return self.name == "bool"

    @property
    def is_void(self) -> bool:
        return self.name == "void"


@dataclass(frozen=True)
class ArrayType(Type):
    """Array types."""

    element_type: Type

    def __str__(self) -> str:  # pragma: no cover - helper for diagnostics
        return f"{self.element_type}[]"


# Frequently used instances for convenience.
INT_TYPE = PrimitiveType("int")
FLOAT_TYPE = PrimitiveType("float")
BOOL_TYPE = PrimitiveType("bool")
VOID_TYPE = PrimitiveType("void")


# ---------------------------------------------------------------------------
# Top-level declarations
# ---------------------------------------------------------------------------


@dataclass
class ASTNode:
    """Base class for all AST nodes that tracks source locations."""

    location: SourceLocation


@dataclass
class Program(ASTNode):
    """A complete Bambusa program."""

    globals: List["GlobalDecl"] = field(default_factory=list)
    functions: List["FunctionDecl"] = field(default_factory=list)


@dataclass
class GlobalDecl(ASTNode):
    """A global variable declaration."""

    type: Type
    name: str
    value: "Expression"


@dataclass
class Parameter(ASTNode):
    type: Type
    name: str


@dataclass
class FunctionDecl(ASTNode):
    name: str
    params: List[Parameter]
    return_type: Type
    body: "Block"


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------


@dataclass
class Statement(ASTNode):
    pass


@dataclass
class Block(Statement):
    statements: List[Statement]


@dataclass
class VarDecl(Statement):
    type: Type
    name: str
    initializer: Optional["Expression"]


@dataclass
class Assignment(Statement):
    name: str
    value: "Expression"


@dataclass
class IfStmt(Statement):
    condition: "Expression"
    then_block: Block
    else_block: Optional[Block]


@dataclass
class Range(ASTNode):
    start: "Expression"
    end: "Expression"


@dataclass
class ForStmt(Statement):
    iterator: str
    range: Range
    body: Block


@dataclass
class ReturnStmt(Statement):
    value: "Expression"


@dataclass
class ExprStmt(Statement):
    value: "Expression"


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


@dataclass
class Expression(ASTNode):
    inferred_type: Optional[Type] = field(default=None, init=False, compare=False)


@dataclass
class Literal(Expression):
    value: Union[int, float, bool]


@dataclass
class Identifier(Expression):
    name: str


@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression


@dataclass
class BinaryOp(Expression):
    operator: str
    left: Expression
    right: Expression


@dataclass
class ConditionalExpr(Expression):
    condition: Expression
    then_expr: Expression
    else_expr: Expression

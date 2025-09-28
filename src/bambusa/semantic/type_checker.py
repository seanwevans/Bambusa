"""Semantic analysis and type checking for Bambusa programs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .. import ast


@dataclass
class SemanticError(Exception):
    """Error raised when semantic analysis fails."""

    message: str
    location: ast.SourceLocation

    def __str__(self) -> str:  # pragma: no cover - formatting helper
        return f"{self.message} (line {self.location.line}, column {self.location.column})"


class _Scope:
    def __init__(self) -> None:
        self.values: Dict[str, ast.Type] = {}

    def define(self, name: str, type_: ast.Type) -> None:
        if name in self.values:
            raise ValueError(f"symbol '{name}' already defined in scope")
        self.values[name] = type_

    def get(self, name: str) -> Optional[ast.Type]:
        return self.values.get(name)


class TypeChecker:
    """Walks the AST and enforces type rules."""

    def __init__(self) -> None:
        self._scopes: List[_Scope] = []
        self._globals: Dict[str, ast.Type] = {}
        self._current_return: Optional[ast.Type] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, program: ast.Program) -> None:
        self._globals.clear()
        self._scopes.clear()

        # Gather globals first so functions can reference them.
        for global_decl in program.globals:
            if global_decl.name in self._globals:
                self._error(global_decl.location, f"global '{global_decl.name}' already defined")
            value_type = self._check_expression(global_decl.value)
            self._ensure_assignable(global_decl.type, value_type, global_decl.value.location)
            self._globals[global_decl.name] = global_decl.type

        # Track function names to avoid duplicates.
        seen_functions: Dict[str, ast.FunctionDecl] = {}
        for function in program.functions:
            if function.name in seen_functions:
                other = seen_functions[function.name]
                self._error(
                    function.location,
                    f"function '{function.name}' already defined on line {other.location.line}",
                )
            seen_functions[function.name] = function

        for function in program.functions:
            self._check_function(function)

    # ------------------------------------------------------------------
    # Scoping utilities
    # ------------------------------------------------------------------

    def _push_scope(self) -> None:
        self._scopes.append(_Scope())

    def _pop_scope(self) -> None:
        self._scopes.pop()

    def _define(self, name: str, type_: ast.Type, location: ast.SourceLocation) -> None:
        scope = self._scopes[-1]
        try:
            scope.define(name, type_)
        except ValueError:
            self._error(location, f"symbol '{name}' already defined in this scope")

    def _lookup(self, name: str, location: ast.SourceLocation) -> ast.Type:
        for scope in reversed(self._scopes):
            found = scope.get(name)
            if found is not None:
                return found
        if name in self._globals:
            return self._globals[name]
        self._error(location, f"unknown identifier '{name}'")

    # ------------------------------------------------------------------
    # Top-level constructs
    # ------------------------------------------------------------------

    def _check_function(self, function: ast.FunctionDecl) -> None:
        self._push_scope()
        self._current_return = function.return_type

        for param in function.params:
            self._define(param.name, param.type, param.location)

        self._check_block(function.body, new_scope=False)

        self._current_return = None
        self._pop_scope()

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _check_block(self, block: ast.Block, *, new_scope: bool = True) -> None:
        if new_scope:
            self._push_scope()
        for statement in block.statements:
            self._check_statement(statement)
        if new_scope:
            self._pop_scope()

    def _check_statement(self, statement: ast.Statement) -> None:
        if isinstance(statement, ast.Block):
            self._check_block(statement)
        elif isinstance(statement, ast.VarDecl):
            self._define(statement.name, statement.type, statement.location)
            if statement.initializer is not None:
                init_type = self._check_expression(statement.initializer)
                self._ensure_assignable(statement.type, init_type, statement.initializer.location)
        elif isinstance(statement, ast.Assignment):
            target_type = self._lookup(statement.name, statement.location)
            value_type = self._check_expression(statement.value)
            self._ensure_assignable(target_type, value_type, statement.value.location)
        elif isinstance(statement, ast.IfStmt):
            condition_type = self._check_expression(statement.condition)
            if not condition_type.is_bool():
                self._error(statement.condition.location, "if condition must be a boolean expression")
            self._check_block(statement.then_block)
            if statement.else_block is not None:
                self._check_block(statement.else_block)
        elif isinstance(statement, ast.ForStmt):
            range_start = self._check_expression(statement.range.start)
            range_end = self._check_expression(statement.range.end)
            for expr, type_ in ((statement.range.start, range_start), (statement.range.end, range_end)):
                if type_ != ast.INT_TYPE:
                    self._error(expr.location, "loop bounds must be integers")
            self._push_scope()
            self._define(statement.iterator, ast.INT_TYPE, statement.location)
            self._check_block(statement.body, new_scope=False)
            self._pop_scope()
        elif isinstance(statement, ast.ReturnStmt):
            if self._current_return is None:
                self._error(statement.location, "return statement outside of a function")
            if self._current_return == ast.VOID_TYPE:
                self._error(statement.location, "void functions cannot return a value")
            value_type = self._check_expression(statement.value)
            self._ensure_assignable(self._current_return, value_type, statement.value.location)
        elif isinstance(statement, ast.ExprStmt):
            self._check_expression(statement.value)
        else:  # pragma: no cover - defensive programming for future nodes
            raise NotImplementedError(f"unhandled statement type: {type(statement)!r}")

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _check_expression(self, expression: ast.Expression) -> ast.Type:
        if isinstance(expression, ast.Literal):
            value = expression.value
            if isinstance(value, bool):
                expression.inferred_type = ast.BOOL_TYPE
            elif isinstance(value, int) and not isinstance(value, bool):
                expression.inferred_type = ast.INT_TYPE
            elif isinstance(value, float):
                expression.inferred_type = ast.FLOAT_TYPE
            else:  # pragma: no cover
                raise AssertionError(f"unexpected literal value: {value!r}")
            return expression.inferred_type

        if isinstance(expression, ast.Identifier):
            type_ = self._lookup(expression.name, expression.location)
            expression.inferred_type = type_
            return type_

        if isinstance(expression, ast.UnaryOp):
            operand_type = self._check_expression(expression.operand)
            if expression.operator == "!":
                if not operand_type.is_bool():
                    self._error(expression.operand.location, "logical negation requires a boolean operand")
                expression.inferred_type = ast.BOOL_TYPE
                return expression.inferred_type
            if expression.operator == "-":
                if not operand_type.is_numeric():
                    self._error(expression.operand.location, "unary minus requires a numeric operand")
                expression.inferred_type = operand_type
                return operand_type
            self._error(expression.location, f"unsupported unary operator '{expression.operator}'")

        if isinstance(expression, ast.BinaryOp):
            left_type = self._check_expression(expression.left)
            right_type = self._check_expression(expression.right)
            op = expression.operator

            if op in {"+", "-", "*", "/"}:
                if not (left_type.is_numeric() and right_type.is_numeric()):
                    self._error(expression.location, f"operator '{op}' requires numeric operands")
                if left_type == ast.FLOAT_TYPE or right_type == ast.FLOAT_TYPE or op == "/":
                    expression.inferred_type = ast.FLOAT_TYPE
                else:
                    expression.inferred_type = ast.INT_TYPE
                return expression.inferred_type

            if op == "%":
                if left_type != ast.INT_TYPE or right_type != ast.INT_TYPE:
                    self._error(expression.location, "operator '%' requires integer operands")
                expression.inferred_type = ast.INT_TYPE
                return expression.inferred_type

            if op in {"<", ">", "<=", ">="}:
                if not (left_type.is_numeric() and right_type.is_numeric()):
                    self._error(expression.location, f"operator '{op}' requires numeric operands")
                expression.inferred_type = ast.BOOL_TYPE
                return expression.inferred_type

            if op in {"==", "!="}:
                if left_type != right_type:
                    self._error(expression.location, "operands to equality must have the same type")
                expression.inferred_type = ast.BOOL_TYPE
                return expression.inferred_type

            if op in {"&&", "||"}:
                if not (left_type.is_bool() and right_type.is_bool()):
                    self._error(expression.location, f"operator '{op}' requires boolean operands")
                expression.inferred_type = ast.BOOL_TYPE
                return expression.inferred_type

            self._error(expression.location, f"unsupported binary operator '{op}'")

        if isinstance(expression, ast.ConditionalExpr):
            condition_type = self._check_expression(expression.condition)
            if not condition_type.is_bool():
                self._error(expression.condition.location, "conditional guard must be boolean")
            then_type = self._check_expression(expression.then_expr)
            else_type = self._check_expression(expression.else_expr)
            if then_type != else_type:
                self._error(expression.location, "conditional branches must yield the same type")
            expression.inferred_type = then_type
            return then_type

        raise NotImplementedError(f"unhandled expression type: {type(expression)!r}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_assignable(self, target: ast.Type, value: ast.Type, location: ast.SourceLocation) -> None:
        if target != value:
            self._error(location, f"cannot assign {value} to {target}")

    def _error(self, location: ast.SourceLocation, message: str) -> None:
        raise SemanticError(message=message, location=location)


def type_check(program: ast.Program) -> None:
    """Convenience wrapper around :class:`TypeChecker`."""

    TypeChecker().check(program)

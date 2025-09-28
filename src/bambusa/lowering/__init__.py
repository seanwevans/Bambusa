"""Lowering from the Bambusa AST into branchless SSA IR."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .. import ast
from ..ir import (
    Binary,
    Compare,
    Constant,
    IRFunction,
    IRProgram,
    LoopIndex,
    Mask,
    MaskedLoad,
    MaskedLoop,
    MaskedStore,
    Operation,
    SSAValue,
    Select,
    Unary,
)
from .utils import SSANamer, compose_masks


class LoweringError(RuntimeError):
    """Raised when the AST contains constructs the lowering pass cannot handle."""


class IRBuilder:
    """Helper for constructing SSA operations while tracking constants and masks."""

    def __init__(self, namer: SSANamer) -> None:
        self.namer = namer
        self.instructions: List[Operation] = []
        self._scalar_literals: Dict[object, SSAValue] = {}
        self._mask_literals: Dict[bool, Mask] = {}
        self.return_value: Optional[SSAValue] = None

    # ------------------------------------------------------------------
    # Literal helpers
    def scalar_constant(self, value: object, *, hint: str = "const") -> SSAValue:
        key = ("scalar", value)
        cached = self._scalar_literals.get(key)
        if cached is not None:
            return cached
        output = SSAValue(self.namer.fresh(hint))
        self.emit(Constant(output=output, value=value))
        self._scalar_literals[key] = output
        return output

    def mask_literal(self, value: bool, *, hint: str = "mask") -> Mask:
        cached = self._mask_literals.get(value)
        if cached is not None:
            return cached
        output = Mask(self.namer.fresh(hint))
        self.emit(Constant(output=output, value=value))
        self._mask_literals[value] = output
        return output

    @property
    def true_mask(self) -> Mask:
        return self.mask_literal(True, hint="true")

    @property
    def false_mask(self) -> Mask:
        return self.mask_literal(False, hint="false")

    # ------------------------------------------------------------------
    # Primitive operations
    def emit(self, operation: Operation) -> None:
        self.instructions.append(operation)

    def binary(self, op: str, left: SSAValue, right: SSAValue, *, hint: str = "bin") -> SSAValue:
        output = SSAValue(self.namer.fresh(hint))
        self.emit(Binary(output=output, op=op, left=left, right=right))
        return output

    def mask_and(self, left: Mask, right: Mask, *, hint: str = "mask_and") -> Mask:
        output = Mask(self.namer.fresh(hint))
        self.emit(Binary(output=output, op="and", left=left, right=right))
        return output

    def mask_not(self, operand: Mask, *, hint: str = "mask_not") -> Mask:
        output = Mask(self.namer.fresh(hint))
        self.emit(Unary(output=output, op="not", operand=operand))
        return output

    def compare(self, op: str, left: SSAValue, right: SSAValue, *, hint: str = "cmp") -> Mask:
        output = Mask(self.namer.fresh(hint))
        self.emit(Compare(output=output, op=op, left=left, right=right))
        return output

    def select(
        self,
        mask: Mask,
        on_true: SSAValue,
        on_false: SSAValue,
        *,
        hint: str = "select",
    ) -> SSAValue:
        output = SSAValue(self.namer.fresh(hint))
        self.emit(Select(output=output, mask=mask, on_true=on_true, on_false=on_false))
        return output

    def masked_load(
        self,
        mask: Mask,
        array: SSAValue,
        index: SSAValue,
        default: SSAValue,
        *,
        hint: str = "load",
    ) -> SSAValue:
        output = SSAValue(self.namer.fresh(hint))
        self.emit(MaskedLoad(output=output, mask=mask, array=array, index=index, default=default))
        return output

    def masked_store(
        self,
        mask: Mask,
        array: SSAValue,
        index: SSAValue,
        value: SSAValue,
    ) -> None:
        self.emit(MaskedStore(output=None, mask=mask, array=array, index=index, value=value))

    def ensure_mask(self, value: SSAValue, *, hint: str = "mask") -> Mask:
        if isinstance(value, Mask):
            return value
        zero = self.scalar_constant(0, hint=f"{hint}_zero")
        return self.compare("!=", value, zero, hint=hint)

    # ------------------------------------------------------------------
    def record_return(self, value: SSAValue, mask: Optional[Mask]) -> None:
        if mask is None or mask == self.true_mask:
            self.return_value = value
            return

        if self.return_value is None:
            base = self.scalar_constant(0, hint="ret_default")
        else:
            base = self.return_value
        merged = self.select(mask, value, base, hint="ret_merge")
        self.return_value = merged


class LoopBuilder(IRBuilder):
    """Specialised builder used to construct masked loop bodies."""

    def __init__(
        self,
        namer: SSANamer,
        *,
        index_hint: str,
        start: SSAValue,
        end: SSAValue,
        base_mask: Optional[Mask],
    ) -> None:
        super().__init__(namer)
        self.index = LoopIndex(self.namer.fresh(f"{index_hint}_idx"))
        self.start = start
        self.end = end
        self.base_mask = base_mask if base_mask is not None else self.true_mask
        bounds = self.compare("<", self.index, self.end, hint=f"{index_hint}_lt_end")
        self.mask = compose_masks(self, self.base_mask, bounds, hint=f"{index_hint}_iter")

    def build(self, outputs: Dict[str, SSAValue]) -> MaskedLoop:
        return MaskedLoop(
            output=None,
            index=self.index,
            start=self.start,
            end=self.end,
            mask=self.mask,
            body=list(self.instructions),
            outputs=outputs,
        )


def assign(
    builder: IRBuilder,
    env: Dict[str, SSAValue],
    name: str,
    value: SSAValue,
    mask: Optional[Mask],
) -> SSAValue:
    if mask is None or mask == builder.true_mask:
        env[name] = value
        return value

    previous = env.get(name)
    if previous is None:
        raise LoweringError(f"Variable '{name}' assigned under mask before definition")
    guarded = builder.select(mask, value, previous, hint=name)
    env[name] = guarded
    return guarded


def lower_expr(
    expr: ast.Expression,
    env: Dict[str, SSAValue],
    builder: IRBuilder,
    mask: Optional[Mask],
) -> SSAValue:
    if isinstance(expr, ast.Literal):
        return builder.scalar_constant(expr.value, hint="lit")
    if isinstance(expr, ast.Var):
        try:
            return env[expr.name]
        except KeyError as exc:  # pragma: no cover - sanity guard
            raise LoweringError(f"Unknown variable '{expr.name}'") from exc
    if isinstance(expr, ast.BinaryOp):
        left = lower_expr(expr.left, env, builder, mask)
        right = lower_expr(expr.right, env, builder, mask)
        return builder.binary(expr.op, left, right, hint=f"{expr.op}_")
    if isinstance(expr, ast.Compare):
        left = lower_expr(expr.left, env, builder, mask)
        right = lower_expr(expr.right, env, builder, mask)
        return builder.compare(expr.op, left, right, hint="cmp")
    if isinstance(expr, ast.Load):
        array = env.get(expr.array)
        if array is None:
            raise LoweringError(f"Unknown array '{expr.array}'")
        index = lower_expr(expr.index, env, builder, mask)
        default = builder.scalar_constant(0, hint=f"{expr.array}_default")
        effective_mask = mask if mask is not None else builder.true_mask
        return builder.masked_load(effective_mask, array, index, default, hint=f"load_{expr.array}")
    raise LoweringError(f"Unsupported expression type: {type(expr)!r}")


def lower_condition(
    expr: ast.Expression,
    env: Dict[str, SSAValue],
    builder: IRBuilder,
    mask: Optional[Mask],
) -> Mask:
    return builder.ensure_mask(lower_expr(expr, env, builder, mask), hint="cond")


def merge_environments(
    builder: IRBuilder,
    base_env: Dict[str, SSAValue],
    then_env: Dict[str, SSAValue],
    else_env: Dict[str, SSAValue],
    cond_mask: Mask,
) -> None:
    keys = set(base_env) | set(then_env) | set(else_env)
    for name in keys:
        base_value = base_env.get(name)
        then_value = then_env.get(name, base_value)
        else_value = else_env.get(name, base_value)

        if then_value is else_value:
            base_env[name] = then_value
            continue
        if then_value is base_value and else_value is not base_value:
            base_env[name] = else_value
            continue
        if else_value is base_value and then_value is not base_value:
            base_env[name] = then_value
            continue
        base_env[name] = builder.select(cond_mask, then_value, else_value, hint=name)


def lower_block(
    statements: Iterable[ast.Statement],
    env: Dict[str, SSAValue],
    builder: IRBuilder,
    mask: Optional[Mask],
) -> None:
    for stmt in statements:
        if isinstance(stmt, ast.Assign):
            value = lower_expr(stmt.value, env, builder, mask)
            assign(builder, env, stmt.target, value, mask)
        elif isinstance(stmt, ast.Store):
            array = env.get(stmt.array)
            if array is None:
                raise LoweringError(f"Unknown array '{stmt.array}'")
            index = lower_expr(stmt.index, env, builder, mask)
            value = lower_expr(stmt.value, env, builder, mask)
            effective_mask = mask if mask is not None else builder.true_mask
            builder.masked_store(effective_mask, array, index, value)
        elif isinstance(stmt, ast.IfElse):
            cond = lower_condition(stmt.condition, env, builder, mask)
            then_mask = compose_masks(builder, mask, cond, hint="then_mask")
            else_mask = compose_masks(builder, mask, builder.mask_not(cond, hint="cond_not"), hint="else_mask")
            then_env = dict(env)
            else_env = dict(env)
            lower_block(stmt.then_body, then_env, builder, then_mask)
            lower_block(stmt.else_body, else_env, builder, else_mask)
            merge_environments(builder, env, then_env, else_env, cond)
        elif isinstance(stmt, ast.ForLoop):
            start = lower_expr(stmt.start, env, builder, mask)
            end = lower_expr(stmt.end, env, builder, mask)
            base_mask = mask if mask is not None else builder.true_mask
            loop_builder = LoopBuilder(
                builder.namer,
                index_hint=stmt.target,
                start=start,
                end=end,
                base_mask=base_mask,
            )
            loop_env = dict(env)
            loop_env[stmt.target] = loop_builder.index
            lower_block(stmt.body, loop_env, loop_builder, loop_builder.mask)
            outputs: Dict[str, SSAValue] = {}
            for name, value in loop_env.items():
                if name == stmt.target:
                    continue
                if env.get(name) is value:
                    continue
                outputs[name] = value
                env[name] = value
            env.pop(stmt.target, None)
            builder.emit(loop_builder.build(outputs))
        elif isinstance(stmt, ast.Return):
            value = lower_expr(stmt.value, env, builder, mask)
            builder.record_return(value, mask)
        else:  # pragma: no cover - future expansion hook
            raise LoweringError(f"Unsupported statement type: {type(stmt)!r}")


def lower_to_ir(program: ast.Program) -> IRProgram:
    functions: List[IRFunction] = []
    for fn in program.functions:
        namer = SSANamer()
        builder = IRBuilder(namer)
        env: Dict[str, SSAValue] = {}
        params: Dict[str, SSAValue] = {}
        for param in fn.params:
            value = SSAValue(namer.fresh(f"{param}_arg"))
            env[param] = value
            params[param] = value
        lower_block(fn.body, env, builder, None)
        functions.append(
            IRFunction(
                name=fn.name,
                params=params,
                body=builder.instructions,
                return_value=builder.return_value,
            )
        )
    return IRProgram(functions)


__all__ = ["lower_to_ir", "LoweringError", "IRBuilder", "LoopBuilder"]

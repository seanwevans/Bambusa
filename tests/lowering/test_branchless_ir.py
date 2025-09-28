"""Regression tests for lowering control flow into branchless IR."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from bambusa import ast
from bambusa.lowering import lower_to_ir
from bambusa.ir import Binary, Compare, Mask, MaskedLoad, MaskedLoop, Select


def _function_body(program: ast.Program):
    ir = lower_to_ir(program)
    assert len(ir.functions) == 1
    return ir.functions[0]


def test_if_lowered_to_select():
    program = ast.Program(
        functions=[
            ast.Function(
                name="max",
                params=("a", "b"),
                body=(
                    ast.Assign("result", ast.Var("a")),
                    ast.IfElse(
                        condition=ast.Compare(ast.Var("a"), ">", ast.Var("b")),
                        then_body=(ast.Assign("result", ast.Var("a")),),
                        else_body=(ast.Assign("result", ast.Var("b")),),
                    ),
                    ast.Return(ast.Var("result")),
                ),
            )
        ]
    )

    fn = _function_body(program)
    compares = [op for op in fn.body if isinstance(op, Compare)]
    assert compares, "The conditional must produce a comparison mask"
    cond_mask = compares[0].output

    selects = [op for op in fn.body if isinstance(op, Select)]
    assert selects, "Lowering should use select to merge branches"
    assert selects[-1].mask == cond_mask


def test_for_loop_lowered_to_masked_fold():
    program = ast.Program(
        functions=[
            ast.Function(
                name="sum_until",
                params=("arr", "limit", "length"),
                body=(
                    ast.Assign("sum", ast.Literal(0)),
                    ast.ForLoop(
                        target="i",
                        start=ast.Literal(0),
                        end=ast.Var("length"),
                        body=(
                            ast.IfElse(
                                condition=ast.Compare(ast.Var("i"), "<", ast.Var("limit")),
                                then_body=(
                                    ast.Assign(
                                        "sum",
                                        ast.BinaryOp(
                                            ast.Var("sum"),
                                            "+",
                                            ast.Load("arr", ast.Var("i")),
                                        ),
                                    ),
                                ),
                                else_body=(),
                            ),
                        ),
                    ),
                    ast.Return(ast.Var("sum")),
                ),
            )
        ]
    )

    fn = _function_body(program)
    loops = [op for op in fn.body if isinstance(op, MaskedLoop)]
    assert loops, "For loops must lower to masked loop descriptors"
    loop = loops[0]

    assert isinstance(loop.mask, Mask)
    assert "sum" in loop.outputs

    compare_ops = [op for op in loop.body if isinstance(op, Compare)]
    assert len(compare_ops) >= 2, "Loop should compare bounds and predicate"

    mask_composes = [op for op in loop.body if isinstance(op, Binary) and op.op == "and"]
    assert mask_composes, "Loop should compose masks with logical and"

    masked_loads = [op for op in loop.body if isinstance(op, MaskedLoad)]
    assert masked_loads, "Array access must be lowered to masked loads"
    mask_outputs = {op.output for op in mask_composes}
    assert masked_loads[0].mask in mask_outputs

    sum_output = loop.outputs["sum"]
    select_ops = [op for op in loop.body if isinstance(op, Select)]
    assert any(op.output == sum_output for op in select_ops), "Fold result must stem from select"

    add_ops = [op for op in loop.body if isinstance(op, Binary) and op.op == "+"]
    assert add_ops, "Accumulator should use an addition binary op"

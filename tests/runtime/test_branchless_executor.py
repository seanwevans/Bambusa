import pytest

from bambusa.runtime.executor import BranchlessExecutor


@pytest.mark.parametrize(
    "opcode,lhs,rhs,expected_mask",
    [
        ("cmp_eq", 4, 4, True),
        ("cmp_eq", 4, 3, False),
        ("cmp_ne", 4, 3, True),
        ("cmp_ne", 5, 5, False),
        ("cmp_lt", 2, 9, True),
        ("cmp_lt", 9, 2, False),
        ("cmp_le", 5, 5, True),
        ("cmp_le", 7, 5, False),
        ("cmp_gt", 8, 1, True),
        ("cmp_gt", 1, 8, False),
        ("cmp_ge", 6, 2, True),
        ("cmp_ge", 2, 6, False),
    ],
)
def test_comparison_opcodes_drive_select(opcode, lhs, rhs, expected_mask) -> None:
    executor = BranchlessExecutor()
    program = [
        {"op": "const", "target": "lhs", "value": lhs},
        {"op": "const", "target": "rhs", "value": rhs},
        {"op": opcode, "target": "mask", "lhs": "lhs", "rhs": "rhs"},
        {"op": "select", "target": "result", "mask": "mask", "true": "lhs", "false": "rhs"},
    ]

    registers = executor.run(program)

    assert isinstance(registers["mask"], bool)
    assert registers["mask"] is expected_mask
    expected_result = lhs if expected_mask else rhs
    assert registers["result"] == expected_result

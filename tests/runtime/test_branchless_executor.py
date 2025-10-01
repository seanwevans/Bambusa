import pytest

from bambusa.runtime.executor import BranchlessExecutor


def _select(executor: BranchlessExecutor, mask, true_value, false_value):
    executor.registers.update({
        "mask": mask,
        "true": true_value,
        "false": false_value,
    })
    return executor._op_select({"mask": "mask", "true": "true", "false": "false"})


def test_op_select_with_scalar_mask() -> None:
    executor = BranchlessExecutor()

    result = _select(executor, True, 1, 2)

    assert result == 1


def test_op_select_with_sequence_mask() -> None:
    executor = BranchlessExecutor()

    result = _select(executor, [True, False, True], [1, 2, 3], [4, 5, 6])

    assert result == (1, 5, 3)


def test_op_select_with_broadcasted_inputs() -> None:
    executor = BranchlessExecutor()
    mask_vector = executor.heap.allocate([True, False, True])

    result = _select(executor, mask_vector, 10, (1, 2, 3))

    assert result == (10, 2, 10)


def test_op_select_raises_on_shape_mismatch() -> None:
    executor = BranchlessExecutor()

    with pytest.raises(ValueError):
        _select(executor, [True, False], [1, 2, 3], [4, 5, 6])

"""Tests for the Bambusa semantic type checker."""

import pytest

from bambusa.parser import parse_program
from bambusa.semantic.type_checker import SemanticError, type_check


def _check(source: str) -> None:
    program = parse_program(source)
    type_check(program)


def test_valid_program_type_checks() -> None:
    source = """
    fn identity(int x) -> int {
        return x;
    }
    """
    _check(source)


def test_if_condition_must_be_boolean() -> None:
    source = """
    fn bad() -> int {
        if 1 then { return 1; } else { return 0; }
    }
    """
    with pytest.raises(SemanticError) as excinfo:
        _check(source)
    assert "if condition" in str(excinfo.value)


def test_arithmetic_requires_numeric_operands() -> None:
    source = """
    fn bad() -> int {
        return true + 1;
    }
    """
    with pytest.raises(SemanticError) as excinfo:
        _check(source)
    assert "requires numeric" in str(excinfo.value)


def test_loop_bounds_must_be_integers() -> None:
    source = """
    fn bad() -> int {
        for i in true..10 {
            return 0;
        }
        return 0;
    }
    """
    with pytest.raises(SemanticError) as excinfo:
        _check(source)
    assert "loop bounds" in str(excinfo.value)


def test_assignment_type_mismatch_raises() -> None:
    source = """
    fn bad() -> int {
        int x;
        x = true;
        return 0;
    }
    """
    with pytest.raises(SemanticError) as excinfo:
        _check(source)
    assert "cannot assign" in str(excinfo.value)

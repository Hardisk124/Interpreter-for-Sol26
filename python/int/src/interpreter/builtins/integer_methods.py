"""
Built-in methods for the SOL26 Integer class.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from interpreter.builtins.helper_methods import _require_block, _require_integer, _sol_bool
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.runtime import SolInteger, SolObject, SolString

if TYPE_CHECKING:
    from interpreter.builtins import BlockEvaluator, BuiltinFn
    from interpreter.class_registry import ClassRegistry


def _int_equal_to(receiver: SolObject, args: list[SolObject],
              registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns true if the receiver and the argument are equal.
    """
    other = _require_integer(args[0], "Integer equalTo")
    receiver = _require_integer(receiver, "Integer equalTo")
    return _sol_bool(receiver.internal_value == other.internal_value)

def _int_greater_than(receiver: SolObject, args: list[SolObject],
                registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns true if the receiver is greater than the argument.
    """
    other = _require_integer(args[0], "Integer greaterThan")
    receiver = _require_integer(receiver, "Integer greaterThan")
    return _sol_bool(receiver.internal_value > other.internal_value)

def _int_plus(receiver: SolObject, args: list[SolObject],
          registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns the sum of the receiver and the argument.
    """
    other = _require_integer(args[0], "Integer plus")
    receiver = _require_integer(receiver, "Integer plus")
    result = receiver.internal_value + other.internal_value
    return SolInteger(receiver.sol_class, result)

def _int_minus(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns the difference of the receiver and the argument.
    """
    other = _require_integer(args[0], "Integer minus")
    receiver = _require_integer(receiver, "Integer minus")
    result = receiver.internal_value - other.internal_value
    return SolInteger(receiver.sol_class, result)

def _int_multiply_by(receiver: SolObject, args: list[SolObject],
              registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns the product of the receiver and the argument."""
    other = _require_integer(args[0], "Integer multiplyBy")
    receiver = _require_integer(receiver, "Integer multiplyBy")
    result = receiver.internal_value * other.internal_value
    return SolInteger(receiver.sol_class, result)

def _int_div_by(receiver: SolObject, args: list[SolObject],
           registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns the division result. Raises error 53 on division by zero."""
    other = _require_integer(args[0], "Integer divBy")
    receiver = _require_integer(receiver, "Integer divBy")
    if other.internal_value == 0:
        raise InterpreterError(ErrorCode.INT_INVALID_ARG, "Division by zero")
    result = receiver.internal_value // other.internal_value
    return SolInteger(receiver.sol_class, result)

def _int_as_string(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns the string representation of the integer."""
    receiver = _require_integer(receiver, "Integer asString")
    return SolString(registry.get_class("String"), str(receiver.internal_value))

def _int_as_integer(receiver: SolObject, args: list[SolObject],
                registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns self."""
    return receiver

def _int_times_repeat(receiver: SolObject, args: list[SolObject],
                registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Evaluates the block argument the number of times specified by the integer.
    The block is evaluated with no arguments on each iteration.
    """
    from interpreter.class_registry import nil

    receiver = _require_integer(receiver, "Integer timesRepeat")
    block = _require_block(args[0], "Integer timesRepeat")
    n = receiver.internal_value
    result : SolObject = nil
    if n > 0:
        for i in range(1,n + 1):
            iter_obj = SolInteger(receiver.sol_class, i)
            result = eval_block(block, [iter_obj])

    return result

def _int_is_number(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """returns true for Integer."""
    return _sol_bool(True)


METHODS: dict[str, BuiltinFn] = {
    "equalTo:":             _int_equal_to,
    "greaterThan:":         _int_greater_than,
    "plus:":                _int_plus,
    "minus:":               _int_minus,
    "multiplyBy:":          _int_multiply_by,
    "divBy:":               _int_div_by,
    "asString":             _int_as_string,
    "asInteger":            _int_as_integer,
    "timesRepeat:":         _int_times_repeat,
    "isNumber":             _int_is_number
}

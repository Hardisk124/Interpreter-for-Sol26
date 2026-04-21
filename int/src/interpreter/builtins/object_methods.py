"""
Built-in methods for the SOL26 Object class.
Author: Martin Turčan <xturcam00@vutbr.cz>
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from int.src.interpreter.builtins.helper_methods import _sol_bool
from int.src.interpreter.runtime import SolInteger, SolObject, SolString

if TYPE_CHECKING:
    from int.src.interpreter.builtins import BlockEvaluator, BuiltinFn
    from int.src.interpreter.class_registry import ClassRegistry

def _obj_identical_to(receiver: SolObject, args: list[SolObject],
                  registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns true if the receiver and the argument are the same object (identity)."""
    return _sol_bool(receiver is args[0])

def _obj_equal_to(receiver: SolObject, args: list[SolObject],
              registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    Returns true if the receiver and the argument are equal (equality)."""
    other = args[0]
    if isinstance(receiver, SolInteger) and isinstance(other, SolInteger):
        return _sol_bool(receiver.internal_value == other.internal_value)
    if isinstance(receiver, SolString) and isinstance(other, SolString):
        return _sol_bool(receiver.internal_value == other.internal_value)
    # Fallback: identity
    return _sol_bool(receiver is other)

def _obj_as_string(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns empty string '' for plain Object."""
    return SolString(registry.get_class("String"), "")

def _obj_is_number(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns false for plain Object."""
    return _sol_bool(False)

def _obj_is_string(receiver: SolObject, args: list[SolObject],
               registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns false for plain Object."""
    return _sol_bool(False)

def _obj_is_block(receiver: SolObject, args: list[SolObject],
              registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns false for plain Object."""
    return _sol_bool(False)

def _obj_is_nil(receiver: SolObject, args: list[SolObject],
             registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns false for plain Object."""
    return _sol_bool(False)

def _obj_is_boolean(receiver: SolObject, args: list[SolObject],
                    registry: ClassRegistry, eval_block: BlockEvaluator) -> SolObject:
    """
    returns false for plain Object."""
    return _sol_bool(False)


METHODS: dict[str, BuiltinFn] = {
    "identicalTo:":         _obj_identical_to,
    "equalTo:":             _obj_equal_to,
    "asString":            _obj_as_string,
    "isNumber":            _obj_is_number,
    "isString":            _obj_is_string,
    "isBlock":             _obj_is_block,
    "isNil":              _obj_is_nil,
    "isBoolean":          _obj_is_boolean
}
